from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from core.models import Wallet, PaymentSession
from core.enums import Chain, Asset
from core.exceptions import WalletAssignmentError
import datetime

class WalletManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_wallet(self, chain: str, asset: str, token_contract: str | None) -> Wallet | None:
        """Atomically find and lock an available wallet for assignment."""
        stmt = (
            select(Wallet)
            .where(
                Wallet.chain == chain,
                Wallet.asset == asset,
                (Wallet.token_contract == token_contract) if token_contract else Wallet.token_contract.is_(None),
                Wallet.is_active == True,
                Wallet.current_session_id.is_(None),
            )
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        return wallet

    async def assign_wallet_to_session(self, session: PaymentSession) -> Wallet:
        wallet = await self.get_available_wallet(session.chain, session.asset, session.token_contract)
        if not wallet:
            raise WalletAssignmentError("No available wallet for selected chain/asset")
        session.wallet_id = wallet.id
        wallet.current_session_id = session.id
        wallet.last_used_at = datetime.datetime.utcnow()
        self.db.add(session)
        self.db.add(wallet)
        await self.db.flush()
        return wallet

    async def release_wallet(self, wallet_id: int):
        await self.db.execute(
            update(Wallet)
            .where(Wallet.id == wallet_id)
            .values(current_session_id=None)
        )
