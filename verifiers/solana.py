from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature
from core.models import Wallet
from core.enums import RejectReason
from .base import BaseVerifier
from core.config import settings

class SolanaVerifier(BaseVerifier):
    chain = "solana"

    def __init__(self, rpc_url: str):
        self.client = AsyncClient(rpc_url)

    async def verify(self, tx_hash: str, wallet: Wallet, expected_amount: int):
        try:
            sig = Signature.from_string(tx_hash)
            tx_resp = await self.client.get_transaction(sig, max_supported_transaction_version=0)
            if tx_resp.value is None:
                return False, 0, RejectReason.FAKE_INVALID_TX
            if tx_resp.value.transaction.meta.err is not None:
                return False, 0, RejectReason.FAKE_FAILED_TX

            # Confirmations: Solana doesn't need multiple, assuming inclusion is final
            if wallet.asset == "native":
                # SOL transfer: check pre/post balances
                meta = tx_resp.value.transaction.meta
                account_keys = tx_resp.value.transaction.transaction.message.account_keys
                wallet_pubkey = Pubkey.from_string(wallet.address)
                index = None
                for i, key in enumerate(account_keys):
                    if key == wallet_pubkey:
                        index = i
                        break
                if index is None:
                    return False, 0, RejectReason.FAKE_WRONG_RECIPIENT
                pre_balance = meta.pre_balances[index]
                post_balance = meta.post_balances[index]
                received = post_balance - pre_balance
                if received >= expected_amount:
                    return True, received, None
                else:
                    return False, received, RejectReason.FAKE_ZERO_VALUE
            else:
                # SPL token transfer: This is a placeholder.
                # Full implementation would parse token balances from meta.
                # For now, we cannot verify without more complex logic.
                # We'll assume failure.
                return False, 0, RejectReason.FAKE_WRONG_TOKEN
        except Exception as e:
            return False, 0, RejectReason.FAKE_INVALID_TX
