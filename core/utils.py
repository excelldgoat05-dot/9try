from decimal import Decimal
from core.enums import Chain, Asset

# Mapping of (chain, asset) to number of decimals
DECIMALS = {
    (Chain.ETHEREUM.value, Asset.NATIVE.value): 18,
    (Chain.ETHEREUM.value, Asset.USDT.value): 6,
    (Chain.ETHEREUM.value, Asset.USDC.value): 6,
    (Chain.BSC.value, Asset.NATIVE.value): 18,
    (Chain.BSC.value, Asset.USDT.value): 18,  # BEP-20 USDT can be 18
    (Chain.BSC.value, Asset.USDC.value): 18,
    (Chain.POLYGON.value, Asset.NATIVE.value): 18,  # MATIC/POL
    (Chain.POLYGON.value, Asset.USDT.value): 6,
    (Chain.POLYGON.value, Asset.USDC.value): 6,
    (Chain.SOLANA.value, Asset.NATIVE.value): 9,
    (Chain.SOLANA.value, Asset.USDT.value): 6,
    (Chain.SOLANA.value, Asset.USDC.value): 6,
    (Chain.TRON.value, Asset.NATIVE.value): 6,  # TRX
    (Chain.TRON.value, Asset.USDT.value): 6,
    (Chain.TRON.value, Asset.USDC.value): 6,
}

def to_base_units(amount: Decimal, chain: str, asset: str) -> int:
    key = (chain, asset)
    if key not in DECIMALS:
        raise ValueError(f"Unknown decimals for {chain}/{asset}")
    decimals = DECIMALS[key]
    return int(amount * (10 ** decimals))

def from_base_units(amount: int, chain: str, asset: str) -> Decimal:
    key = (chain, asset)
    if key not in DECIMALS:
        raise ValueError(f"Unknown decimals for {chain}/{asset}")
    decimals = DECIMALS[key]
    return Decimal(amount) / (10 ** decimals)

def format_amount(amount: int, chain: str, asset: str) -> str:
    return f"{from_base_units(amount, chain, asset)} {asset.upper()}"
