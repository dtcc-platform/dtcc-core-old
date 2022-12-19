import os
from pymongo import MongoClient
from logger import getLogger

logger = getLogger(__file__)

host =   os.environ.get("MONGODB_HOST", "localhost")
user = os.environ.get("MONGODB_USER", "dtcc_admin" )
password = os.environ.get("MONGODB_PASSWORD", "dtcc_mongo")
db_name = os.environ.get("MONGODB_DATABASE", "dtcc3d")

URI = f"mongodb://{user}:{password}@{host}:27017/"

class MongodbService():
    def __init__(self, table_name="tasks") -> None:
        try:
            self.mongodb_client = MongoClient(URI)
            self.database = self.mongodb_client[db_name]
            self.table = table_name
            logger.info("Connected to the MongoDB database!")
        except:
            logger.exception("from starting mongodb service")

    def insert(self, data:dict):
        new_task = self.database[self.table].insert_one(data)
        inserted_task = self.database[self.table].find_one(
            {"_id": new_task.inserted_id}
        )

        return inserted_task

    def list_items(self):
        tasks = list(self.database[self.table].find(limit=100))
        return tasks

    def find(self, query:dict):
        if (item := self.database[self.table].find(query)) is not None:
            return item
        return {}

    ## TODO add a delete method and get item based on key and value
    def delete(self, key, value):
        return {}

    def close(self):
        self.mongodb_client.close()

def test():
    client = MongodbService(table_name="tasks")
    # data = {
    #     "id":123,
    #     "value": "akbdkb",
    #     "l": [1,2,3],
    #     "run":True
    # }

    # t1 = client.insert(data=data)

    # data = {
    #     "id":123,
    #     "value": "akbhd",
    #     "l": [1,2,3],
    #     "run":True
    # }

    # t2 = client.insert(data=data)

    print(len(client.list_items()))



if __name__=='__main__':
    test()