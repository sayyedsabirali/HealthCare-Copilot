from pymongo import MongoClient
from backend.config.settings import settings


class MongoDB:

    def __init__(self):
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.DATABASE_NAME]

    def get_database(self):
        return self.db


mongodb = MongoDB()

# expose database
db = mongodb.get_database()


# optional helper
def get_database():
    return db