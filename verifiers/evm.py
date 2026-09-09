import asyncio
from web3 import Web3
from web3.exceptions import TransactionNotFound
from core.models import Wallet
from core.enums import RejectReason
from .base import BaseVerifier
from core.config import settings

class EVMVerifier(BaseVerifier):
    def __init__(self, rpc_url: str, chain: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.chain = chain

    async def verify(self, tx_hash: str, wallet: Wallet, expected_amount: int):
        loop = asyncio.get_event_loop()
        tx_data = await loop.run_in_executor(None, self._get_tx, tx_hash)
        if not tx_data:
            return False, 0, RejectReason.FAKE_INVALID_TX

        # Check confirmations
        required = settings.CONFIRMATIONS_REQUIRED.get(self.chain, 1)
        if tx_data["confirmations"] < required:
            return False, 0, RejectReason.FAKE_UNCONFIRMED

        # Check status
        if tx_data["receipt"].status != 1:
            return False, 0, RejectReason.FAKE_FAILED_TX

        # Verify transfer
        if wallet.asset == "native":
            # Native currency (ETH, BNB, MATIC)
            if tx_data["to"] and tx_data["to"].lower() == wallet.address.lower():
                if tx_data["value"] >= expected_amount:
                    return True, tx_data["value"], None
                else:
                    return False, tx_data["value"], RejectReason.FAKE_ZERO_VALUE  # underpaid, but we treat as not success
            else:
                return False, 0, RejectReason.FAKE_WRONG_RECIPIENT
        else:
            # ERC-20 token
            receipt = tx_data["receipt"]
            token_contract = wallet.token_contract.lower()
            transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            for log in receipt.logs:
                if log.address.lower() == token_contract:
                    if len(log.topics) == 3 and log.topics[0].hex() == transfer_topic:
                        to_addr = "0x" + log.topics[2].hex()[-40:]
                        if to_addr.lower() == wallet.address.lower():
                            amount = int(log.data.hex(), 16)
                            if amount >= expected_amount:
                                return True, amount, None
                            else:
                                return False, amount, RejectReason.FAKE_ZERO_VALUE
            return False, 0, RejectReason.FAKE_WRONG_TOKEN

    def _get_tx(self, tx_hash):
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                "hash": tx_hash,
                "from": tx["from"],
                "to": tx.get("to"),
                "value": tx.get("value", 0),
                "confirmations": self.w3.eth.block_number - receipt.blockNumber + 1,
                "receipt": receipt,
            }
        except TransactionNotFound:
            return None
