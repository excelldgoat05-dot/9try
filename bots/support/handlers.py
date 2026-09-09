from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from core.config import settings

router = Router()

@router.message(Command("support"))
async def cmd_support(message: Message):
    await message.answer("Please describe your issue. A support ticket will be created.")
