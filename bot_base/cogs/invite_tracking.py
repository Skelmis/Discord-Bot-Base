import logging
from typing import Dict, cast, List, Set

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

log = logging.getLogger(__name__)


class InviteTracking(Cog):
    """Invite tracking hooks."""

    def __init__(self, bot: BotBase):
        super().__init__(bot)
        self.invite_cache: Dict[str, Invite] = self.bot.invite_cache
        self.invite_document: Document = self.bot.db.invite_tracking

    async def async_init(self) -> None:
        """Hooks the database layer in."""
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

    async def save_invite(self, invite: Invite) -> None:
        """Save the provided invite."""
        self.invite_cache[invite.invite_id] = invite
        await self.invite_document.upsert(invite.as_filter(), invite.as_dict())

    async def delete_guild(self, guild_id: int) -> None:
        self.invite_cache = {
            k: v for k, v in self.invite_cache.items() if v.guild_id != guild_id
        }
        await self.invite_document.delete(EQ("guild_id", guild_id))

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
                    guild_id=guild.id,
                )
            else:
                current_invite.uses = invite.uses

            await self.save_invite(current_invite)

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
            created_by=invite.inviter.id,
        )
        await self.save_invite(internal_invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        try:
            self.invite_cache.pop(invite.id)
        except KeyError:
            pass

        await self.invite_document.delete(
            AQ(
                AND(
                    EQ("invite_id", invite.id),
                    EQ("guild_id", invite.guild.id),
                ),
            )
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        for current_invite in await member.guild.invites():
            for cached_invite in self.invite_cache.values():
                if (
                    current_invite.id == cached_invite.invite_id
                    and current_invite.uses - cached_invite.uses == 1
                ):
                    cached_invite.uses += 1
                    cached_invite.invited_members.add(member.id)
                    await self.save_invite(cached_invite)
                    return

        log.warning(
            "Could not figure out who invited Member(id=%s, guild_id=%s)",
            member.id,
            member.guild.id,
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        for cached_invite in self.invite_cache.values():
            if cached_invite.used_by(member.id):
                cached_invite.invited_members.discard(member.id)
                cached_invite.previously_invited_members.append(member.id)
                await self.save_invite(cached_invite)
                return
