from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Boolean, Integer, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base
import datetime

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    chain = Column(String, nullable=False, index=True)
    address = Column(String, nullable=False, unique=True, index=True)
    asset = Column(String, nullable=False)  # native, usdt, usdc
    token_contract = Column(String, nullable=True)  # for tokens
    is_active = Column(Boolean, default=True, index=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    current_session_id = Column(Integer, ForeignKey("payment_sessions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("PaymentSession", back_populates="wallet", foreign_keys="PaymentSession.wallet_id")

    __table_args__ = (
        UniqueConstraint('chain', 'address', name='uix_chain_address'),
        Index('ix_wallets_chain_asset_active', 'chain', 'asset', 'is_active'),
    )

class PaymentSession(Base):
    __tablename__ = "payment_sessions"
    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(BigInteger, nullable=False, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    chain = Column(String, nullable=False)
    asset = Column(String, nullable=False)
    token_contract = Column(String, nullable=True)
    expected_amount = Column(BigInteger, nullable=False)  # base units
    received_amount = Column(BigInteger, default=0, nullable=False)
    status = Column(String, default="active", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    membership_id = Column(Integer, nullable=True)
    metadata = Column(JSONB, nullable=True)

    wallet = relationship("Wallet", back_populates="sessions", foreign_keys=[wallet_id])
    payments = relationship("Payment", back_populates="session")

    __table_args__ = (
        Index('ix_sessions_user_status', 'telegram_user_id', 'status'),
    )

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("payment_sessions.id"), nullable=False, index=True)
    chain = Column(String, nullable=False)
    tx_hash = Column(String, nullable=False)
    amount_received = Column(BigInteger, nullable=False)  # base units
    status = Column(String, default="pending")
    reject_reason = Column(String, nullable=True)
    confirmations = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("PaymentSession", back_populates="payments")

    __table_args__ = (
        UniqueConstraint('chain', 'tx_hash', name='uix_chain_txhash'),
    )

class ProcessedTransaction(Base):
    __tablename__ = "processed_transactions"
    id = Column(Integer, primary_key=True)
    chain = Column(String, nullable=False)
    tx_hash = Column(String, nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('chain', 'tx_hash', name='uix_processed_tx'),
    )

class MembershipGrant(Base):
    __tablename__ = "membership_grants"
    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(BigInteger, nullable=False, index=True)
    membership_id = Column(Integer, nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(Integer, ForeignKey("payment_sessions.id"), nullable=True)
    amount_paid = Column(BigInteger, nullable=False)
