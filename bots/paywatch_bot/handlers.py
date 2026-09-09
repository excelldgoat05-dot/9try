from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.models import PaymentSession, Payment
from core.enums import SessionStatus, PaymentStatus
from core.config import settings
from sqlalchemy import select
import datetime

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

@router.message(Command("stats"))
async def cmd_stats(message: Message, db: AsyncSession = Depends(get_db)):
    if not is_admin(message.from_user.id):
        await message.reply("Unauthorized")
        return
    # Simple stats
    total_sessions = await db.execute(select(func.count(PaymentSession.id)))
    total_sessions = total_sessions.scalar()
    completed = await db.execute(select(func.count(PaymentSession.id)).where(PaymentSession.status == SessionStatus.COMPLETED.value))
    completed = completed.scalar()
    total_received = await db.execute(select(func.sum(PaymentSession.received_amount)))
    total_received = total_received.scalar() or 0

    await message.answer(
        f"Total sessions: {total_sessions}\n"
        f"Completed: {completed}\n"
        f"Total received (base units): {total_received}"
    )

@router.message(Command("review_late"))
async def cmd_review_late(message: Message, db: AsyncSession = Depends(get_db)):
    if not is_admin(message.from_user.id):
        await message.reply("Unauthorized")
        return
    # Find sessions in LATE_PAYMENT_REVIEW or expired with funds
    now = datetime.datetime.utcnow()
    stmt = select(PaymentSession).where(
        PaymentSession.status == SessionStatus.LATE_PAYMENT_REVIEW.value,
        PaymentSession.received_amount > 0
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    if not sessions:
        await message.reply("No late payment reviews pending.")
        return
    for s in sessions:
        await message.answer(f"Session {s.id}, user {s.telegram_user_id}, received {s.received_amount} base units, expected {s.expected_amount}")
