import pytest
from core.models import Wallet, PaymentSession, Payment
from core.enums import Chain, Asset

@pytest.mark.asyncio
async def test_create_wallet(db_session):
    wallet = Wallet(chain=Chain.ETHEREUM.value, address="0x123", asset=Asset.NATIVE.value)
    db_session.add(wallet)
    await db_session.commit()
    assert wallet.id is not None
