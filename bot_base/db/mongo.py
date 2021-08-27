from motor.motor_asyncio import AsyncIOMotorClient

from bot_base.db.document import Document


class MongoManager:
    def __init__(self, connection_url, database_name=None):
        database_name = database_name or "production"

        self.__mongo = AsyncIOMotorClient(connection_url)
        self.db = self.__mongo[database_name]

    def __getattr__(self, item) -> Document:
        """
        Parameters
        ----------
        item : str
            Denotes the 'table' to return

        Returns
        -------
        Document
            A Document made for said item
        """
        doc = Document(self.db, item)
        setattr(self, item, doc)

        return doc
