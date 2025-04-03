import logging

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from filters import IsAdmin
from models import DB

router = Router()


@router.message(IsAdmin(), CommandStart())
async def start_handler(message: Message):
    with DB() as db:
        db.add_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Бот запущен и готов к работе.")


@router.message(IsAdmin(), Command("myid"))
async def my_id_handler(message: Message):
    await message.answer(f"Ваш телеграмм ID: <code>{message.from_user.id}</code>")


@router.message(IsAdmin(), Command("add_admin"))
async def add_admin_handler(message: Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Не указано ID юзера")
        return
    admin_id = command_parts[1]
    try:
        with DB() as db:
            db.add_admin(admin_id)
    except Exception as e:
        await message.answer("Уже добавлен")
        logging.info(e)
        return

    await message.answer("✅ Админ добавлен")


@router.message(IsAdmin(), Command("add_word"))
async def add_word_handler(message: Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Не указано ключевое слово")
        return
    word = command_parts[1]
    with DB() as db:
        db.add_keyword(word)

    await message.answer("✅ Слово добавлен")


@router.message(IsAdmin(), Command("add_group"))
async def add_group_handler(message: Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Не указано ссылка на группу")
        return
    group_link = command_parts[1]
    with DB() as db:
        db.add_group(group_link)

    await message.answer("✅ Группа добавлен")


@router.message(IsAdmin(), Command("admins"))
async def admins_list_handler(message: Message):
    with DB() as db:
        admins = db.get_all_admins()
    await message.answer(f"Список админов: \n\n{admins}")


@router.message(IsAdmin(), Command("words"))
async def words_list_handler(message: Message):
    with DB() as db:
        keywords = db.get_all_keywords()
    await message.answer(f"Список фраз: \n\n{keywords}")


@router.message(IsAdmin(), Command("groups"))
async def groups_list_handler(message: Message):
    with DB() as db:
        groups = db.get_all_groups()
    await message.answer(f"Список группы: \n\n{groups}", disable_web_page_preview=True)
