from aiogram.filters import BaseFilter
from aiogram.types import Message

from models import DB
from parser import ADMIN_IDS


class IsAdmin(BaseFilter):

    async def __call__(self, message: Message) -> bool:
        with DB() as db:
            admins = db.get_all_admins(make_list=True)
            return message.from_user.id in ADMIN_IDS.append(admins)