from pymongo.mongo_client import MongoClient

client = MongoClient("REMOVED_KEY")

db = client.todo_db

collection_name = db["todo_collection"]