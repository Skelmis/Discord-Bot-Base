from bot_base.db import MongoManager


class BlacklistManager:
    def __init__(self, db: MongoManager):
        self.db = db

        self.users = set()
        self.guilds = set()

    def __contains__(self, item: int) -> bool:
        """
        Checks whether an id is contained within
        an internal blacklist or not
        """
        assert isinstance(item, int)

        in_users = item in self.users
        in_guilds = item in self.guilds

        return in_users or in_guilds

    async def initialize(self) -> None:
        """
        Called sometime on creation in order to
        populate the internal blacklist.
        """
        all_guild_entries = await self.db.guild_blacklist.get_all()
        for guild in all_guild_entries:
            self.guilds.add(guild["_id"])

        all_user_entries = await self.db.user_blacklist.get_all()
        for user in all_user_entries:
            self.users.add(user["_id"])

    async def add_to_blacklist(
        self, item: int, reason: str = "Unknown", is_guild_blacklist: bool = True
    ) -> None:
        """
        Add a given int to the internal blacklist
        as well as persist it within the db
        """
        assert isinstance(item, int)

        if is_guild_blacklist:
            self.guilds.add(item)
            await self.db.guild_blacklist.upsert({"_id": item, "reason": reason})

        else:
            self.users.add(item)
            await self.db.user_blacklist.upsert({"_id": item, "reason": reason})

    async def remove_from_blacklist(
        self, item: int, is_guild_blacklist: bool = True
    ) -> None:
        """
        Removes a given blacklist, ignoring if
        they weren't blacklisted
        """
        assert isinstance(item, int)

        if is_guild_blacklist:
            self.guilds.discard(item)
            await self.db.guild_blacklist.delete({"_id": item})

        else:
            self.users.discard(item)
            await self.db.user_blacklist.delete({"_id": item})
