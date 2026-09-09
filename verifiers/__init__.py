from core.config import settings
from .evm import EVMVerifier
from .solana import SolanaVerifier
from .tron import TronVerifier

verifiers = {
    "ethereum": EVMVerifier(settings.ETH_RPC_URL, "ethereum"),
    "bsc": EVMVerifier(settings.BSC_RPC_URL, "bsc"),
    "polygon": EVMVerifier(settings.POLYGON_RPC_URL, "polygon"),
    "solana": SolanaVerifier(settings.SOLANA_RPC_URL),
    "tron": TronVerifier(settings.TRON_RPC_URL),
}

def get_verifier(chain: str):
    return verifiers.get(chain)
