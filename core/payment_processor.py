from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from core.models import PaymentSession, Payment, ProcessedTransaction, Wallet, MembershipGrant
from core.enums import SessionStatus, PaymentStatus, RejectReason
from core.exceptions import DuplicateTransactionError
from verifiers import get_verifier
from core.config import settings
import datetime

class PaymentProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_payment(self, session_id: int, tx_hash: str) -> Payment:
        """Verify a transaction for a given session. Idempotent."""
        # Check if transaction already processed (idempotency)
        session = await self.db.get(PaymentSession, session_id)
        if not session:
            raise ValueError("Session not found")

        chain = session.chain
        existing_processed = await self.db.execute(
            select(ProcessedTransaction).where(
                ProcessedTransaction.chain == chain,
                ProcessedTransaction.tx_hash == tx_hash
            )
        )
        if existing_processed.scalar_one_or_none():
            # Return existing payment result if any
            payment = await self.db.execute(
                select(Payment).where(
                    Payment.chain == chain,
                    Payment.tx_hash == tx_hash,
                    Payment.session_id == session_id
                )
            )
            return payment.scalar_one_or_none()

        verifier = get_verifier(chain)
        wallet = await self.db.get(Wallet, session.wallet_id)
        success, received_base_units, reject_reason = await verifier.verify(
            tx_hash, wallet, session.expected_amount
        )

        # Create payment record
        payment = Payment(
            session_id=session.id,
            chain=chain,
            tx_hash=tx_hash,
            amount_received=received_base_units,
            status=PaymentStatus.CONFIRMED.value if success else PaymentStatus.FAILED.value,
            reject_reason=reject_reason if not success else None,
        )
        self.db.add(payment)
        # Mark as processed
        processed = ProcessedTransaction(chain=chain, tx_hash=tx_hash)
        self.db.add(processed)

        # Update session
        if success:
            session.received_amount += received_base_units
            if session.received_amount >= session.expected_amount:
                session.status = SessionStatus.COMPLETED.value
                session.completed_at = datetime.datetime.utcnow()
                # Release wallet
                await self.db.execute(
                    update(Wallet).where(Wallet.id == session.wallet_id).values(current_session_id=None)
                )
                # Grant membership
                grant = MembershipGrant(
                    telegram_user_id=session.telegram_user_id,
                    membership_id=session.membership_id,
                    session_id=session.id,
                    amount_paid=session.received_amount,
                )
                self.db.add(grant)
            else:
                session.status = SessionStatus.UNDERPAID.value
        else:
            # Rejected
            session.status = SessionStatus.FAKE.value

        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def process_underpaid_accumulation(self, session_id: int):
        """Check if underpaid session now has enough total confirmed payments."""
        session = await self.db.get(PaymentSession, session_id)
        if session and session.status == SessionStatus.UNDERPAID.value:
            total_stmt = select(func.sum(Payment.amount_received)).where(
                Payment.session_id == session.id,
                Payment.status == PaymentStatus.CONFIRMED.value
            )
            total_result = await self.db.execute(total_stmt)
            total_amount = total_result.scalar() or 0
            if total_amount >= session.expected_amount:
                session.received_amount = total_amount
                session.status = SessionStatus.COMPLETED.value
                session.completed_at = datetime.datetime.utcnow()
                # Release wallet
                await self.db.execute(
                    update(Wallet).where(Wallet.id == session.wallet_id).values(current_session_id=None)
                )
                # Grant membership
                grant = MembershipGrant(
                    telegram_user_id=session.telegram_user_id,
                    membership_id=session.membership_id,
                    session_id=session.id,
                    amount_paid=total_amount,
                )
                self.db.add(grant)
                await self.db.commit()
                return True
        return False
