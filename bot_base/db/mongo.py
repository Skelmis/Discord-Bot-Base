import datetime
import logging
from typing import List, Dict

from alaric import Document
from motor.motor_asyncio import AsyncIOMotorClient


log = logging.getLogger(__name__)


class MongoManager:
    def __init__(self, connection_url, database_name=None):
        self.database_name = database_name or "production"

        self.__mongo = AsyncIOMotorClient(connection_url)
        self.db = self.__mongo[self.database_name]

        # Documents
        self.user_blacklist = Document(self.db, "user_blacklist")
        self.guild_blacklist = Document(self.db, "guild_blacklist")

    def typed_lookup(self, attr: str) -> Document:
        return getattr(self, attr)

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
        doc: Document = Document(self.db, item)
        setattr(self, item, doc)

        return doc

    def get_current_documents(self) -> List[Document]:
        class_vars = vars(self)
        documents = []
        for v in class_vars.values():
            if isinstance(v, Document):
                documents.append(v)

        return documents

    async def run_backup(self):
        """
        Backs up the database within the same cluster.
        """
        documents: List[Document] = self.get_current_documents()

        epoch: str = str(round(datetime.datetime.utcnow().timestamp()))
        name = f"backup-{epoch}"
        backup_db = self.__mongo[name]
        log.info("Backing up the database, this backup is '%s'", name)

        for document in documents:
            backup_doc: Document = Document(backup_db, document.document_name)
            all_data: List[Dict] = await document.get_all()
            if not all_data:
                continue

            await backup_doc.bulk_insert(all_data)
