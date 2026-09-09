import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal
from core.session_manager import SessionManager
from core.payment_processor import PaymentProcessor
from core.models import PaymentSession
from core.enums import SessionStatus
from core.config import settings

logger = logging.getLogger(__name__)

async def check_expired_sessions():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                sm = SessionManager(db)
                await sm.check_expired_sessions()
                await db.commit()
        except Exception as e:
            logger.error(f"Error in check_expired_sessions: {e}")
        await asyncio.sleep(60)

async def check_underpaid_accumulation():
    """Check underpaid sessions if total now meets required amount."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Find underpaid sessions
                result = await db.execute(
                    select(PaymentSession).where(PaymentSession.status == SessionStatus.UNDERPAID.value)
                )
                underpaid_sessions = result.scalars().all()
                for session in underpaid_sessions:
                    processor = PaymentProcessor(db)
                    await processor.process_underpaid_accumulation(session.id)
                await db.commit()
        except Exception as e:
            logger.error(f"Error in check_underpaid_accumulation: {e}")
        await asyncio.sleep(300)

async def main():
    tasks = [
        check_expired_sessions(),
        check_underpaid_accumulation(),
        # Add more background tasks as needed
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
