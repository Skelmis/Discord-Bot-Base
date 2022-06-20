from typing import Dict


class Vanity:
    """
    Represents a Vanity invite for a guild.

    Attributes
    ----------
    guild_id: int
        The id of this guild
    guild_name: str
        The name of this guild
    """

    def __init__(self, guild_id: int, guild_name: str):
        self.guild_id: int = guild_id
        self.guild_name: str = guild_name

    def __repr__(self):
        return f"Vanity url for Guild(id={self.guild_id}, name={self.guild_name})"

    def as_dict(self) -> Dict:
        return {"guild_id": self.guild_id, "guild_name": self.guild_name}
