import asyncio
from aiogram import Bot, Dispatcher
from typing import List
from pymongo import MongoClient
from utils import convert_datetime_to_date
import time
from emoji import emojize
from constants import TYPES_EN_RU, TYPES_RU_EN


def find_limits_for_tasks(bot: Bot, loop) -> None:

    client = MongoClient("localhost", 27017)
    db = client.wb_data
    warehouses = db["warehouse_limits"]
    tasks = db["tasks"]

    while True:
        for task in tasks.find():
            time.sleep(1)
            if task.get("isActive"):
                for warehouse in warehouses.find():
                    if task.get("warehouseName") == warehouse.get("displayName"):
                        is_task_completable = process_warehouse_limits(task, warehouse.get("limits"))
                        if is_task_completable:
                            # Отправить сообщение о том что задание выполнено
                            # Установить статус сообщения неактивно
                            tasks.update_one({"_id": task.get("_id")}, {"$set": {"isActive": False}})
                            date_range = (
                                f'с {task.get("requestedDate")[0]} по \
                                {task.get("requestedDate")[-1]}'
                                if isinstance(task.get("requestedDate"), list)
                                else task.get("requestedDate")
                            )

                            asyncio.run_coroutine_threadsafe(bot.send_message(task.get("user_id"),
                                emojize(
                                    f':tada: На запрашиваемом складе есть место для вашего заказа! :tada:\
                                \n:package: Количество {task.get("quantity")} \
                                \n:office: Склад {task.get("warehouseName")} \
                                \n:email: Тип поставки {task.get("deliveryType")} \
                                \n:clock9: Дата поиска лимита {date_range}',
                                    language="alias",
                                )
                            ), loop)


def process_warehouse_limits(task: dict, limits: List[dict]) -> bool:
    for limit in limits:
        if limit.get(TYPES_RU_EN[task["deliveryType"]]) >= task.get("quantity"):
            if isinstance(task.get("requestedDate"), list):
                if convert_datetime_to_date(limit.get("date")) in task.get("requestedDate"):
                    return True
            else:
                if convert_datetime_to_date(limit.get("date")) == task.get("requestedDate"):
                    return True
    return False



if __name__ == "__main__":
    find_limits_for_tasks()
