# config.py
import json
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ALCHEMY_API_KEY: str
    ALCHEMY_NETWORK: str = "eth-mainnet"
    ALCHEMY_CORE_URL: str = ""
    ALCHEMY_NFT_URL: str = ""
    ALCHEMY_PRICE_URL: str = ""
    ETHERSCAN_API_URL: str = "https://api.etherscan.io/v2/api"
    ETHERSCAN_API_KEY: str
    BITQUERY_URL: str = "https://streaming.bitquery.io/graphql"
    
    BITQUERY_TOKEN: str
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
    POAP_CONTRACT: str = "0x22C1f6050E56d2876009903609a2cC3fEf83B415"
    ENS_NAMEWRAPPER: str = "0xD4416b13d2b3a9aBae7AcD5D6C2BbDBE25686401"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base = f"https://{self.ALCHEMY_NETWORK}.g.alchemy.com"
        self.ALCHEMY_CORE_URL = f"{base}/v2/{self.ALCHEMY_API_KEY}"
        self.ALCHEMY_NFT_URL = f"{base}/nft/v3/{self.ALCHEMY_API_KEY}"
        self.ALCHEMY_PRICE_URL = f"{base}/prices/v1/{self.ALCHEMY_API_KEY}/tokens/by-address"
        url = f"https://api.g.alchemy.com/prices/v1/{self.ALCHEMY_API_KEY}/tokens/by-address"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Add this line to ignore extra fields

# Known addresses
MIXER_ADDRESSES = [
    "0x0000000000000000000000000000000000000000",  # Null address (example mixer)
    "0x8589427373d6d84e98730d7795d8f6f8731fda16",  # Tornado Cash Router
    "0x722122df12d4e14e13ac3b6895a86e84145b6967",  # Tornado Cash
    "0xdd4c48c0b24039969fc16d1cdf626eab821d3384",  # Tornado Cash
]

STABLECOINS = {
    "usdc": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "usdt": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "dai": "0x6b175474e89094c44da98b954eedeac495271d0f",
}

BLUE_CHIP_NFTS = [
    "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",  # BAYC
    "0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb",  # CryptoPunks
    "0xed5af388653567af2f388e6224dc7c4b3241c544",  # Azuki
    "0x60e4d786628fea6478f785a6d7e704777c86a7c6",  # MAYC
    "0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b",  # CloneX
]

def load_protocol_addresses(path: str = "protocol.txt") -> dict:
    file_path = Path(path)
    if not file_path.exists():
        return {}

    with open(file_path, "r") as f:
        return json.load(f)

DEFI_PROTOCOLS = load_protocol_addresses()