from typing import Dict, cast

from alaric import Document

from bot_base import Cog, BotBase
from bot_base.db import Invite


class InviteTracking(Cog):
    """Invite tracking hooks."""

    def __init__(self, bot: BotBase):
        super().__init__(bot)
        self.invite_cache: Dict[str, Invite] = {}
        self.invite_document: Document = self.bot.db.invite_tracking

    async def async_init(self) -> None:
        """Hooks the database layer in."""
        for invite in await self.invite_document.get_all():
            invite = cast(Invite, invite)
            self.invite_cache[invite.invite_id] = invite

    async def save_invite(self, invite: Invite) -> None:
        """Save the provided invite."""
        await self.invite_document.upsert(invite.as_filter(), invite.as_dict())
