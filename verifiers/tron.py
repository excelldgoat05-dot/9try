from tronpy import AsyncTron
from tronpy.providers import AsyncHTTPProvider
from core.models import Wallet
from core.enums import RejectReason
from .base import BaseVerifier
from core.config import settings

class TronVerifier(BaseVerifier):
    chain = "tron"

    def __init__(self, rpc_url: str):
        self.client = AsyncTron(provider=AsyncHTTPProvider(rpc_url))

    async def verify(self, tx_hash: str, wallet: Wallet, expected_amount: int):
        try:
            tx = await self.client.get_transaction(tx_hash)
            if not tx:
                return False, 0, RejectReason.FAKE_INVALID_TX
            if tx.get("ret") and tx["ret"][0]["contractRet"] != "SUCCESS":
                return False, 0, RejectReason.FAKE_FAILED_TX
            # Confirmations: assume 1 after inclusion
            if wallet.asset == "native":
                # TRX transfer
                for contract in tx["raw_data"]["contract"]:
                    if contract["type"] == "TransferContract":
                        value = contract["parameter"]["value"]
                        to_addr = self.client.address.from_hex(value["to_address"])
                        if to_addr == wallet.address:
                            amount = value["amount"]  # in sun
                            if amount >= expected_amount:
                                return True, amount, None
                            else:
                                return False, amount, RejectReason.FAKE_ZERO_VALUE
                return False, 0, RejectReason.FAKE_WRONG_RECIPIENT
            else:
                # TRC-20 token: This is a placeholder.
                # Full implementation would parse event logs.
                return False, 0, RejectReason.FAKE_WRONG_TOKEN
        except Exception:
            return False, 0, RejectReason.FAKE_INVALID_TX
