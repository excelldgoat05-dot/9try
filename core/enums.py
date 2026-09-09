from enum import Enum

class Chain(str, Enum):
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    SOLANA = "solana"
    TRON = "tron"

class Asset(str, Enum):
    NATIVE = "native"
    USDT = "usdt"
    USDC = "usdc"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING_VERIFICATION = "pending_verification"
    COMPLETED = "completed"
    UNDERPAID = "underpaid"
    OVERPAID = "overpaid"
    FAKE = "fake"
    LATE_PAYMENT_REVIEW = "late_payment_review"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"

class RejectReason(str, Enum):
    FAKE_WRONG_CHAIN = "wrong_chain"
    FAKE_WRONG_RECIPIENT = "wrong_recipient"
    FAKE_WRONG_TOKEN = "wrong_token"
    FAKE_FAILED_TX = "failed_tx"
    FAKE_UNCONFIRMED = "unconfirmed"
    FAKE_ZERO_VALUE = "zero_value"
    FAKE_ALREADY_USED = "already_used"
    FAKE_INVALID_TX = "invalid_tx"
