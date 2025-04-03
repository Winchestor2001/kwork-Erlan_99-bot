import json
import asyncio
import logging
import re

from telethon import TelegramClient, events
from telethon.errors import RPCError, FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest
from config import config
from aiogram import Bot

from models import DB

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# # Загружаем список групп
# with open("groups.json", "r", encoding="utf-8") as f:
#     GROUPS = json.load(f)
#
# # Загружаем ключевые слова
# with open("keywords.json", "r", encoding="utf-8") as f:
#     KEYWORDS = set(json.load(f))

client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)
bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

ADMIN_IDS = list(map(int, config.ADMIN_IDS.split(",")))  # Конвертируем строку в список чисел
GROUPS = DB().get_all_groups(make_list=True)
KEYWORDS = DB().get_all_keywords(make_list=True)


def is_relevant_post(message_text: str) -> bool:
    """Проверяет, соответствует ли сообщение ключевым фразам."""
    text = message_text.lower().strip()  # Переводим сообщение в нижний регистр

    return any(re.search(re.escape(phrase), text) for phrase in KEYWORDS)  # Ищем ключевую фразу в любом месте


async def join_groups():
    """Автоматически вступает в группы перед началом парсинга, если бот ещё не в них."""
    async with client:
        bot_user = await client.get_me()  # Загружаем информацию о боте

        for group in GROUPS:
            try:
                logging.info(f"🔎 Проверяем группу: {group}")

                try:
                    entity = await client.get_entity(group)  # Пробуем получить информацию о группе
                except ValueError:
                    logging.warning(f"❌ Группа {group} недоступна. Возможно, она приватная или удалена.")
                    continue  # Пропускаем и идём дальше

                # Проверяем, является ли группа каналом (в каналах нельзя получить список участников)
                if entity.broadcast:
                    logging.info(f"🔹 {group} - это канал. Пропускаем проверку участников.")
                    continue  # Каналы пропускаем

                # Проверяем, состоит ли бот в группе
                if entity.left:
                    logging.info(f"🚀 Бот НЕ в группе {group}, пробуем вступить...")
                    await client(JoinChannelRequest(group))  # Вступаем в группу
                    logging.info(f"✅ Успешно вступил в {group}")
                    await asyncio.sleep(5)  # Даём Телеграму обновить список

            except FloodWaitError as e:
                logging.warning(f"⏳ FloodWait: Ожидание {e.seconds} секунд перед повторной попыткой...")
                await asyncio.sleep(e.seconds)  # Ждём и пробуем снова
            except RPCError as e:
                logging.error(f"⚠️ Ошибка RPC в группе {group}: {e}")
            except Exception as e:
                logging.error(f"⚠️ Ошибка при вступлении в {group}: {e}")


async def send_to_admins(text):
    """Отправляет найденное сообщение всем администраторам."""
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, disable_web_page_preview=True)
            logging.info(f"📨 Сообщение отправлено админу {admin_id}")
        except Exception as e:
            logging.error(f"❌ Ошибка отправки сообщения админу {admin_id}: {e}")


async def process_message(event):
    """Обрабатывает новые сообщения и создаёт ссылку на пост."""

    # Проверяем, не является ли сообщение системным
    if event.message.action:
        logging.info(f"🔕 Игнорируем системное сообщение: {event.message.text}")
        return

    message_text = event.message.message.strip()

    if is_relevant_post(message_text):
        chat = await event.get_chat()  # Получаем информацию о группе
        message_id = event.message.id

        # Проверяем, является ли группа публичной (есть username)
        if chat.username:
            message_link = f"https://t.me/{chat.username}/{message_id}"  # Работает для публичных групп
        else:
            message_link = f"(Приватная группа, chat_id: {event.chat_id}, message_id: {message_id})"

        alert_text = (
            f"🔔 Найдено подходящее сообщение:\n\n"
            f"{message_text}\n\n"
            f"🔗 Ссылка на сообщение: {message_link}"
        )

        logging.info(f"🚀 Подходит: {alert_text}")
        await send_to_admins(alert_text)

    else:
        logging.info(f"❌ Сообщение не подходит: {message_text}")


async def start_parser():
    """Асинхронно запускает Telethon-клиент, вступает в группы и начинает мониторинг."""
    global GROUPS

    logging.info("🔄 Вступление в группы перед мониторингом...")
    await join_groups()  # Автовступление

    # Обновляем список групп после вступления
    updated_groups = []
    async with client:
        for group in GROUPS:
            try:
                entity = await client.get_input_entity(group)  # Получаем ID группы
                updated_groups.append(entity)
                logging.info(f"✅ Будет мониториться: {group}")
            except Exception as e:
                logging.warning(f"⚠️ Не удалось получить ID для {group}: {e}")

    GROUPS = updated_groups  # Обновляем список групп, которые можно мониторить

    if not GROUPS:
        logging.error("❌ Нет доступных групп для мониторинга! Проверь groups.json и доступ.")
        return

    @client.on(events.NewMessage(chats=GROUPS))
    async def handler(event):
        await process_message(event)

    while True:
        try:
            logging.info("🚀 Запуск парсера...")
            await client.start()
            await client.run_until_disconnected()
        except FloodWaitError as e:
            logging.warning(f"⏳ FloodWait: Ожидание {e.seconds} секунд перед повторным запуском...")
            await asyncio.sleep(e.seconds)
        except RPCError as e:
            logging.warning(f"⚠️ Ошибка RPC: {e}. Переподключение через 5 секунд...")
            await asyncio.sleep(5)
        except Exception as e:
            logging.error(f"❌ Ошибка в парсере: {e}")
            await asyncio.sleep(10)


def run_parser():
    """Запускает Telethon-клиент в отдельном asyncio-цикле."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_parser())
