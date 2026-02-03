# models.py
from pydantic import BaseModel
from typing import List, Optional

class WalletRequest(BaseModel):
    wallet_address: str

class AssetTransferParams(BaseModel):
    fromBlock: str = "0x0"
    toBlock: str = "latest"
    category: List[str] = ["external", "erc20", "erc721", "erc1155"]
    excludeZeroValue: bool = True
    maxCount: str = "0x3e8"  # 1000 in hex