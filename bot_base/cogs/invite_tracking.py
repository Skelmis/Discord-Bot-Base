from __future__ import annotations

import asyncio
import logging
from typing import Dict, cast, List, Set, TYPE_CHECKING

from alaric import Document, AQ
from alaric.comparison import EQ
from alaric.logical import AND
from alaric.projections import PROJECTION, SHOW


try:
    import nextcord as discord
    from nextcord.ext import commands
except ModuleNotFoundError:
    import disnake as discord
    from disnake.ext import commands

from bot_base import Cog, BotBase
from bot_base.db import Invite

if TYPE_CHECKING:
    from bot_base.wraps import WrappedMember

log = logging.getLogger(__name__)


class InviteTracking(Cog):
    """Invite tracking hooks."""

    def __init__(self, bot: BotBase):
        super().__init__(bot)
        self.invite_cache: Dict[str, Invite] = self.bot.invite_cache
        self.invite_document: Document = self.bot.db.invite_tracking

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.__class__.__name__}: Ready")

    async def async_init(self) -> None:
        """Hooks the database layer in."""
        await self.bot.wait_until_ready()

        for invite in await self.invite_document.get_all():
            invite = cast(Invite, invite)
            self.invite_cache[invite.invite_id] = invite

        # Load all guilds we are now in, but don't have
        # an invitation for yet
        persisted_guilds: List[Dict] = await self.invite_document.find_many(
            {}, projections=PROJECTION(SHOW("guild_id")), try_convert=False
        )
        persisted_guilds: Set[int] = set([d["guild_id"] for d in persisted_guilds])
        current_guilds: Set[int] = set()
        for guild in self.bot.guilds:
            current_guilds.add(guild.id)
            if guild.id not in persisted_guilds:
                await self.load_guild(guild)

        # Delete guilds we have 'left'
        for guild_id in persisted_guilds:
            if guild_id not in current_guilds:
                await self.delete_guild(guild_id)

        log.debug("Initialized invite tracking")

    async def save_invite(self, invite: Invite) -> None:
        """Save the provided invite."""
        self.invite_cache[invite.invite_id] = invite
        await self.invite_document.upsert(invite.as_filter(), invite.as_dict())
        log.debug("Saved invite %s for guild %s", invite.invite_id, invite.guild_id)

    async def delete_guild(self, guild_id: int) -> None:
        self.invite_cache = {
            k: v for k, v in self.invite_cache.items() if v.guild_id != guild_id
        }
        await self.invite_document.delete(EQ("guild_id", guild_id))
        log.debug("Deleted all invites for guild %s", guild_id)

    async def load_guild(self, guild: discord.Guild) -> None:
        """Load a guilds invites into the system."""
        try:
            invites: List[discord.Invite] = await guild.invites()
        except discord.Forbidden:
            log.error(
                "I cannot track invites in Guild(id=%s, name=%s) "
                "as I am missing permissions.",
                guild.id,
                guild.name,
            )
            return

        for invite in invites:
            try:
                current_invite: Invite = self.invite_cache[invite.id]
            except KeyError:
                current_invite: Invite = Invite(
                    invite.id,
                    created_by=invite.inviter.id,
                    uses=invite.uses,
                    max_uses=invite.max_uses,
                    guild_id=guild.id,
                )
            else:
                current_invite.uses = invite.uses

            await self.save_invite(current_invite)

        log.debug(
            "Loaded current invites for Guild(id=%s, name=%s)",
            guild.id,
            guild.name,
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.load_guild(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.delete_guild(guild.id)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        internal_invite: Invite = Invite(
            invite.id,
            guild_id=invite.guild.id,
            uses=invite.uses,
            max_uses=invite.max_uses,
            created_by=invite.inviter.id,
        )
        await self.save_invite(internal_invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        # We can't delete invites as we may need them for
        # member joins, an event which is called *after*
        # this event...
        #
        # We also need to persist them in order
        # to actually tell what invite someone used
        return

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        possible_invites: List[Invite] = []
        all_invites: List[discord.Invite] = await member.guild.invites()
        for current_invite in all_invites:
            for cached_invite in self.invite_cache.values():
                if (
                    current_invite.id == cached_invite.invite_id
                    and current_invite.uses - cached_invite.uses == 1
                ):
                    # Catch all for uses
                    possible_invites.append(cached_invite)
                    continue

                elif (
                    current_invite.id == cached_invite.invite_id
                    and current_invite.max_uses == 1
                    and cached_invite.uses == 0
                    and current_invite.uses == 1
                ):
                    # One time usage invite
                    possible_invites.append(cached_invite)
                    continue

        # Figure out if theres any invites no longer in the guild
        # I.e. they got used
        all_invite_ids = set([invite.id for invite in all_invites])
        for cached_invite in self.invite_cache.values():
            if cached_invite.guild_id != member.guild.id:
                continue

            if cached_invite.invite_id not in all_invite_ids:
                possible_invites.append(cached_invite)

        total_plausible_invites: int = len(possible_invites)
        if not total_plausible_invites:
            log.warning(
                "Could not figure out who invited Member(id=%s, guild_id=%s)",
                member.id,
                member.guild.id,
            )

        elif total_plausible_invites > 1:
            log.warning(
                "Could not figure out who invited Member(id=%s, guild_id=%s) "
                "as there are %s plausible invites it could be",
                member.id,
                member.guild.id,
                total_plausible_invites,
            )

        elif total_plausible_invites == 1:
            cached_invite = possible_invites[0]
            cached_invite.uses += 1
            cached_invite.invited_members.add(member.id)
            await self.save_invite(cached_invite)

        else:
            log.error("Shrugs, not sure how we got here")

    @commands.Cog.listener()
    async def on_member_remove(self, member: WrappedMember):
        for cached_invite in self.invite_cache.values():
            if cached_invite.used_by(member.id):
                member._inviter = None
                cached_invite.invited_members.discard(member.id)
                cached_invite.previously_invited_members.append(member.id)
                await self.save_invite(cached_invite)
                return


def setup(bot):
    bot.add_cog(InviteTracking(bot))
