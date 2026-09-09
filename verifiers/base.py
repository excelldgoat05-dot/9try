from abc import ABC, abstractmethod
from typing import Tuple, Optional
from core.models import Wallet
from core.enums import RejectReason

class BaseVerifier(ABC):
    chain: str

    @abstractmethod
    async def verify(self, tx_hash: str, wallet: Wallet, expected_amount: int) -> Tuple[bool, int, Optional[RejectReason]]:
        """
        Verify a transaction.
        Returns (success, received_amount_in_base_units, reject_reason_if_any)
        """
        pass
