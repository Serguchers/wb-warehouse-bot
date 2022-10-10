from pymongo import MongoClient
from typing import Union

client = MongoClient("localhost", 27017)
db = client.wb_data
collection = db["tasks"]


class TaskConstructor:
    def __init__(self, db) -> None:
        self.isActive: bool = True

    def set_user(self, user_id):
        self.user_id: int = user_id

    def set_warehouseName(self, warehouseName):
        self.warehouseName: str = warehouseName

    def set_deliveryType(self, deliveryType):
        deliveryTypes = {"Монопалеты": "limitPallet", "Короба": "limitMonoMix", "Суперсейф": "limitSupersafe"}
        self.deliveryType: str = deliveryTypes.get(deliveryType)

    def set_requestedDate(self, requestedDate):
        self.requestedDate: Union[str, list[str]] = requestedDate

    def set_quantity(self, quantity):
        self.quantity: int = quantity


if __name__ == "__main__":
    # task = TaskConstructor()
    # task.set_user(123)
    # task.set_deliveryType("my")
    # task.set_quantity(10)
    # task.set_requestedDate('10-01-2022')
    # task.set_warehouseName("test")
    # task.save_task()
    for i in collection.find():
        print(i)
