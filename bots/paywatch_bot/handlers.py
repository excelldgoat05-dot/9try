from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.models import Wallet, PaymentSession
from core.enums import SessionStatus, Chain, Asset
from core.config import settings
from sqlalchemy import select, func
import datetime

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

@router.message(Command("add_wallet"))
async def cmd_add_wallet(message: Message, db: AsyncSession = Depends(get_db)):
    if not is_admin(message.from_user.id):
        await message.reply("Unauthorized")
        return

    parts = message.text.split()
    if len(parts) < 4:
        await message.reply(
            "Usage: /add_wallet <chain> <asset> <address> [token_contract]\n"
            "Example: /add_wallet ethereum usdt 0x123... 0xcontract"
        )
        return

    chain = parts[1].lower()
    asset = parts[2].lower()
    address = parts[3]
    token_contract = parts[4] if len(parts) > 4 else None

    valid_chains = [c.value for c in Chain]
    valid_assets = [a.value for a in Asset]
    if chain not in valid_chains:
        await message.reply(f"Invalid chain. Valid: {', '.join(valid_chains)}")
        return
    if asset not in valid_assets:
        await message.reply(f"Invalid asset. Valid: {', '.join(valid_assets)}")
        return

    existing = await db.execute(
        select(Wallet).where(Wallet.chain == chain, Wallet.address == address)
    )
    if existing.scalar_one_or_none():
        await message.reply("Wallet already exists.")
        return

    wallet = Wallet(
        chain=chain,
        address=address,
        asset=asset,
        token_contract=token_contract if asset != Asset.NATIVE.value else None,
        is_active=True,
    )
    db.add(wallet)
    await db.commit()
    await message.reply(f"Wallet added:\nChain: {chain}\nAsset: {asset}\nAddress: {address}")

@router.message(Command("stats"))
async def cmd_stats(message: Message, db: AsyncSession = Depends(get_db)):
    if not is_admin(message.from_user.id):
        await message.reply("Unauthorized")
        return
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
