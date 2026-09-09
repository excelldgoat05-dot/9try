from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.session_manager import SessionManager
from core.payment_processor import PaymentProcessor
from core.utils import to_base_units, from_base_units
from core.enums import Chain, Asset, SessionStatus
from core.models import Wallet, PaymentSession
from decimal import Decimal
from core.config import settings
from core.logging import logger
from sqlalchemy import select

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Welcome! Use /pay to start a payment.")

@router.message(Command("pay"))
async def cmd_pay(message: Message, db: AsyncSession = Depends(get_db)):
    # In a real bot, you'd ask the user for membership type and chain/asset.
    # Here we use a hardcoded example: 10 USDT on Ethereum.
    user_id = message.from_user.id
    membership_id = 1
    chain = Chain.ETHEREUM.value
    asset = Asset.USDT.value
    token_contract = "0xdAC17F958D2ee523a2206206994597C13D831ec7"  # USDT on Ethereum
    amount_decimal = Decimal("10")

    amount_base = to_base_units(amount_decimal, chain, asset)

    sm = SessionManager(db)
    try:
        session = await sm.create_session(
            user_id=user_id,
            chain=chain,
            asset=asset,
            token_contract=token_contract,
            amount_base_units=amount_base,
            membership_id=membership_id,
        )
        wallet = await db.get(Wallet, session.wallet_id)
        expiry_minutes = settings.PAYMENT_SESSION_TTL_MINUTES
        text = (
            f"Please send exactly {amount_decimal} {asset.upper()} to:\n"
            f"`{wallet.address}`\n"
            f"Chain: {chain}\n"
            f"Expires in {expiry_minutes} minutes.\n"
            f"After sending, submit TX hash with /verify <tx_hash>"
        )
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        await message.answer("Sorry, no wallets available at the moment. Please try later.")

@router.message(Command("verify"))
async def cmd_verify(message: Message, db: AsyncSession = Depends(get_db)):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: /verify <tx_hash>")
        return
    tx_hash = args[1]
    user_id = message.from_user.id

    # Find active or underpaid session for user
    stmt = select(PaymentSession).where(
        PaymentSession.telegram_user_id == user_id,
        PaymentSession.status.in_([SessionStatus.ACTIVE.value, SessionStatus.UNDERPAID.value])
    ).order_by(PaymentSession.created_at.desc()).limit(1)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        await message.reply("No active payment session found.")
        return

    processor = PaymentProcessor(db)
    try:
        payment = await processor.verify_payment(session.id, tx_hash)
        if payment.status == PaymentStatus.CONFIRMED.value:
            await message.reply("Payment confirmed! Access granted.")
        else:
            reason = payment.reject_reason
            await message.reply(f"Payment rejected: {reason}")
    except Exception as e:
        logger.error(f"Verification error: {e}")
        await message.reply("An error occurred during verification. Please contact support.")
