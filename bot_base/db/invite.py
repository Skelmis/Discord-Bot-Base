from __future__ import annotations

from typing import List, Set, Dict, Union

from alaric import Document
from alaric.comparison import EQ

from bot_base.vanity import Vanity


class Invite:
    """Represents a Guild invite."""

    def __init__(
        self,
        invite_id: str,
        *,
        uses: int,
        max_uses: int,
        guild_id: int,
        created_by: Union[int, Vanity],
        invited_members: List[int] = None,
        previously_invited_members: List[int] = None,
        **kwargs,
    ):
        self.uses: int = uses
        self.max_uses: int = max_uses
        self.guild_id: int = guild_id
        self.invite_id: str = invite_id
        self.created_by: Union[int, Vanity] = (
            created_by
            if isinstance(created_by, int)
            else Vanity(**created_by)  # type: ignore # Its a dict from db
            if isinstance(created_by, dict)
            else created_by
        )
        self.invited_members: Set[int] = (
            set(invited_members) if invited_members else set()
        )
        # Maintaining as a list allows for invite abuse checks etc
        self.previously_invited_members: List[int] = (
            previously_invited_members if previously_invited_members else []
        )

    @classmethod
    async def load(cls, invite_id: str, database: Document) -> Invite:
        return await database.find(EQ("invite_id", invite_id))

    def as_dict(self) -> Dict:
        creator = (
            self.created_by
            if isinstance(self.created_by, int)
            else self.created_by.as_dict()
        )

        return {
            "max_uses": self.max_uses,
            "invite_id": self.invite_id,
            "guild_id": self.guild_id,
            "uses": self.uses,
            "created_by": creator,
            "invited_members": list(self.invited_members),
            "previously_invited_members": self.previously_invited_members,
        }

    def as_filter(self) -> Dict:
        return {"invite_id": self.invite_id, "guild_id": self.guild_id}

    def used_by(self, member_id: int) -> bool:
        """Did the member use this invite to join?

        Parameters
        ----------
        member_id: int
            The member we want to check

        Returns
        -------
        bool
            True if they joined with this invite
        """
        return member_id in self.invited_members
