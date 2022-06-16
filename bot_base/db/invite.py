from __future__ import annotations

from typing import List, Set, Dict

from alaric import Document
from alaric.comparison import EQ


class Invite:
    def __init__(
        self,
        invite_id: str,
        *,
        uses: int,
        guild_id: int,
        created_by: int,
        invited_members: List[int] = None,
        previously_invited_members: List[int] = None,
        **kwargs,
    ):
        self.uses: int = uses
        self.guild_id: int = guild_id
        self.invite_id: str = invite_id
        self.created_at: int = created_by
        self.invited_members: Set[int] = (
            set(invited_members) if invited_members else set()
        )
        # Maintaining as a list allows for invite abuse checks etc
        self.previously_invited_members: List[int] = (
            previously_invited_members if previously_invited_members else []
        )

    """Represents a Guild invite."""

    @classmethod
    async def load(cls, invite_id: str, database: Document) -> Invite:
        return await database.find(EQ("invite_id", invite_id))

    def as_dict(self) -> Dict:
        return {
            "invite_id": self.invite_id,
            "guild_id": self.guild_id,
            "uses": self.uses,
            "created_by": self.created_at,
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
