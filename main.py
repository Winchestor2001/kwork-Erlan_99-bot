import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import config
from models import DB
from parser import run_parser
from handlers import router

bot = Bot(token=config.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode='html'))
dp = Dispatcher()


async def main():
    loop = asyncio.get_running_loop()
    loop.create_task(asyncio.to_thread(run_parser))
    with DB() as db:
        db.create_tables()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
