from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.constants import DATABASE_NAME

import logging

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self, connection_string: str):
        try:
            self.client = MongoClient(connection_string)
            self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB!")

            self.database = self.client[DATABASE_NAME]
        except ConnectionFailure as e:
            raise RuntimeError("Could not connect to MongoDB") from e

    def get_database(self):
        return self.database

    def get_collection(self, name: str):
        collection = self.database[name]
        return collection
