from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Union
from typing import Iterable, List
from constants import TYPES_EN_RU


def convert_datetime_to_date(date_time):
    try:
        result = datetime.strptime(date_time, "%Y-%m-%d")
    except ValueError as v:
        unconverted = v.args[0].split(" ")[-1]
        result = datetime.strptime(date_time.replace(unconverted, ""), "%Y-%m-%d")
        result = result.strftime("%Y-%m-%d")
    return result


def set_date(value: str) -> Union[str, list]:
    if value == "Сегодня":
        return datetime.today().strftime("%Y-%m-%d")
    elif value == "Завтра":
        date = datetime.today()
        tommorow = date + timedelta(days=1)
        return tommorow.strftime("%Y-%m-%d")
    elif value == "Неделя":
        dates = []
        date = datetime.today()
        for i in range(1, 8):
            day = date + timedelta(days=i)
            day = day.strftime("%Y-%m-%d")
            dates.append(day)

        return dates


def current_user_tasks(tasks: Iterable) -> List:
    result = []
    for idx, task in enumerate(tasks):
        if task["isActive"]:
            date_range = (
                f"с {task['requestedDate'][0]} по {task['requestedDate'][-1]}"
                if isinstance(task["requestedDate"], list)
                else task["requestedDate"]
            )
            task_string = f"{idx+1}) {task.get('warehouseName')} {date_range} - {task.get('quantity')}шт. {task.get('deliveryType')}"
            result.append(task_string)
        else:
            continue
    return result


if __name__ == "__main__":
    from pymongo import MongoClient

    client = MongoClient("localhost", 27017)
    db = client.wb_data
    warehouses = db["warehouse_limits"]
    tasks = db["tasks"]

    current_user_tasks(tasks.find({"user_id": 423299319}))
