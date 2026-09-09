import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .handlers import router
from core.config import settings
from core.logging import logger

async def main():
    bot = Bot(token=settings.ADDER_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    logger.info("Starting Adder Bot")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
