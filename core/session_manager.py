from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from core.models import PaymentSession, Wallet
from core.enums import SessionStatus
from core.wallet_manager import WalletManager
from core.exceptions import WalletAssignmentError
import datetime
from core.config import settings

class SessionManager:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_manager = WalletManager(db)

    async def create_session(self, user_id: int, chain: str, asset: str,
                             token_contract: str | None, amount_base_units: int,
                             membership_id: int) -> PaymentSession:
        """Create a new payment session and assign an available wallet."""
        session = PaymentSession(
            telegram_user_id=user_id,
            chain=chain,
            asset=asset,
            token_contract=token_contract,
            expected_amount=amount_base_units,
            status=SessionStatus.ACTIVE.value,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.PAYMENT_SESSION_TTL_MINUTES),
            membership_id=membership_id,
        )
        # Assign wallet (locks row)
        wallet = await self.wallet_manager.assign_wallet_to_session(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def expire_session(self, session_id: int):
        """Mark session as expired and release wallet."""
        session = await self.db.get(PaymentSession, session_id)
        if session and session.status == SessionStatus.ACTIVE.value:
            session.status = SessionStatus.EXPIRED.value
            # Release wallet
            await self.wallet_manager.release_wallet(session.wallet_id)
            await self.db.commit()

    async def check_expired_sessions(self):
        """Find and expire all sessions past their expiration."""
        now = datetime.datetime.utcnow()
        stmt = select(PaymentSession).where(
            PaymentSession.expires_at < now,
            PaymentSession.status == SessionStatus.ACTIVE.value
        )
        result = await self.db.execute(stmt)
        expired_sessions = result.scalars().all()
        for session in expired_sessions:
            await self.expire_session(session.id)
