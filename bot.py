import aiogram
import asyncio
from utils import set_date, current_user_tasks
from find_limits_for_task import  find_limits_for_tasks
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from pymongo import MongoClient
from multiprocessing import Process
from threading import Thread
import time
from emoji import emojize
from constants import TYPES_EN_RU


API_TOKEN = ""

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

client = MongoClient("localhost", 27017)
db = client.wb_data
warehouses = db["warehouse_limits"]
tasks = db["tasks"]
warehouses: list = [warehouse.get("displayName") for warehouse in warehouses.find()]


class UserState(StatesGroup):
    username = State()
    set_warehouse = State()
    set_deliveryType = State()
    set_quantity = State()
    set_requestedDate = State()
    finish_creating = State()
    delete_task = State()


@dp.message_handler(commands=["start"])
@dp.message_handler(state=UserState.username)
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    await state.update_data(user_id=user_id)
    add_task_button = KeyboardButton("Добавить задание")
    rm_task_button = KeyboardButton("Удалить задание")

    start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(add_task_button).add(rm_task_button)

    user_tasks = current_user_tasks(tasks.find({"user_id": message.from_user.id}))
    if isinstance(user_tasks, list):
        user_tasks_string = "\n".join(user_tasks)

    await message.reply(
        emojize(
            f"Здравствуйте! :wave: \
        \nСписок активных заданий:\
            \n{user_tasks_string}",
            language="alias",
        ),
        reply_markup=start_keyboard,
    )
    await state.update_data(username=message.from_user.id)
    await UserState.set_warehouse.set()


@dp.message_handler(state=UserState.set_warehouse)
async def send_warehouse_list(message: types.Message, state: FSMContext):
    if message.text == "Удалить задание":
        user_tasks = current_user_tasks(tasks.find({"user_id": message.from_user.id}))
        first_row = [KeyboardButton(i + 1) for i in range(len(user_tasks)) if i < 5]
        second_row = [KeyboardButton(i + 1) for i in range(len(user_tasks)) if i >= 5]
        delete_keyboadoard = ReplyKeyboardMarkup()
        delete_keyboadoard.row(*first_row)
        delete_keyboadoard.row(*second_row)
        await message.reply("Выберите какое задание удалить", reply_markup=delete_keyboadoard)
        await UserState.delete_task.set()
    else:
        user_tasks = current_user_tasks(tasks.find({"user_id": message.from_user.id}))
        if len(user_tasks) >= 10:
            await message.reply("У вас слишком много заданий, лимит - 10!")
            # Удалить задание keyboard
        else:
            warehouses_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            for warehouse in warehouses:
                warehouses_keyboard.add(KeyboardButton(warehouse))

            await message.reply("Выберите склад", reply_markup=warehouses_keyboard)
            await UserState.set_deliveryType.set()


@dp.message_handler(state=UserState.delete_task)
async def delete_task(message: types.Message, state: FSMContext):
    user_tasks = tasks.find({"user_id": message.from_user.id})
    task_to_delete = list(user_tasks).pop(int(message.text) - 1)
    tasks.delete_one(task_to_delete)

    await message.reply(emojize(f"Задание успешно удалено!", language="alias"), reply_markup=ReplyKeyboardRemove())
    await state.finish()
    await UserState.username.set()


@dp.message_handler(state=UserState.set_deliveryType)
async def send_delivery_type(message: types.Message, state: FSMContext):
    await state.update_data(warehouseName=message.text)

    deliveryType_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    deliveryTypes = ["Короба", "Монопалеты", "Суперсейф"]
    for deliveryType in deliveryTypes:
        deliveryType_keyboard.add(KeyboardButton(deliveryType))
    deliveryType_keyboard.add(KeyboardButton("Назад"))

    await message.reply("Выберите тип доставки", reply_markup=deliveryType_keyboard)
    await UserState.set_quantity.set()


@dp.message_handler(state=UserState.set_quantity)
async def send_quantity(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await UserState.set_warehouse.set()
    else:

        await message.reply("Укажите количество")
        await UserState.set_requestedDate.set()
        await state.update_data(deliveryType=message.text)


@dp.message_handler(state=UserState.set_requestedDate)
async def select_date(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await UserState.set_deliveryType.set()

    else:
        await state.update_data(quantity=int(message.text))

        date_choice = ["Сегодня", "Завтра", "Неделя"]
        date_keyboard = ReplyKeyboardMarkup(resize_keyboard=False)
        for dateButton in date_choice:
            date_keyboard.add(KeyboardButton(dateButton))

        await message.reply("Выберите дату", reply_markup=date_keyboard.add(KeyboardButton("Назад")))
        await UserState.finish_creating.set()


@dp.message_handler(state=UserState.finish_creating)
async def finish_creating_task(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await UserState.set_quantity.set()
    else:
        date = set_date(message.text)
        await state.update_data(requestedDate=date)
        data = await state.get_data()
        data["isActive"] = True

        date_range = (
            f"с {data['requestedDate'][0]} по {data['requestedDate'][-1]}"
            if isinstance(data["requestedDate"], list)
            else data["requestedDate"]
        )

        tasks.insert_one(data)

        await message.reply(
            emojize(
                f'Запрос на поиск лимита успешно создан! :tada: \
        \n:package: Количество - {data["quantity"]} \
        \n:office: Склад - {data["warehouseName"]} \
        \n:email: Тип поставки - {data["deliveryType"]} \
        \n:clock9: Дата поиска лимита - {date_range}',
                language="alias",
            ),
            reply_markup=ReplyKeyboardRemove(),
        )

        await state.finish()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # p = Process(target=runner, args=(find_limits_for_tasks, bot))
    # p_1 = Process(target=executor.start_polling, kwargs={"dispatcher": dp, "skip_updates": True})
    # p_1.start()
    # time.sleep(5)
    # p.start()
    t = Thread(target=find_limits_for_tasks, args=(bot, loop))
    t.start()
    executor.start_polling(dp, loop=loop, skip_updates=True)
