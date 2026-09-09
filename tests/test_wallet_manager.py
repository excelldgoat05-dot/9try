import pytest
from core.wallet_manager import WalletManager
from core.models import Wallet
from core.enums import Chain, Asset

@pytest.mark.asyncio
async def test_get_available_wallet(db_session):
    # Add a wallet
    wallet = Wallet(chain=Chain.ETHEREUM.value, address="0xabc", asset=Asset.NATIVE.value)
    db_session.add(wallet)
    await db_session.commit()

    wm = WalletManager(db_session)
    available = await wm.get_available_wallet(Chain.ETHEREUM.value, Asset.NATIVE.value, None)
    assert available is not None
    assert available.address == "0xabc"
