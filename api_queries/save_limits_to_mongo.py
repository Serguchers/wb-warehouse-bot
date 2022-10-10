import json
from pymongo import MongoClient

client = MongoClient("localhost", 27017)

db = client.wb_data

collection = db["warehouse_limits"]
collection.delete_many({})

with open("wb-bot/api_queries/warehouse_limits.json", encoding="utf-8") as f:
    wb_limits_data = json.load(f)

result = collection.insert_many(wb_limits_data)

print(collection.find_one())
