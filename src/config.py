# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ALCHEMY_API_KEY: str
    ALCHEMY_NETWORK: str = "eth-mainnet"
    ALCHEMY_CORE_URL: str = ""
    ALCHEMY_NFT_URL: str = ""
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
    POAP_CONTRACT: str = "0x22C1f6050E56d2876009903609a2cC3fEf83B415"
    ENS_NAMEWRAPPER: str = "0xD4416b13d2b3a9aBae7AcD5D6C2BbDBE25686401"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base = f"https://{self.ALCHEMY_NETWORK}.g.alchemy.com"
        self.ALCHEMY_CORE_URL = f"{base}/v2/{self.ALCHEMY_API_KEY}"
        self.ALCHEMY_NFT_URL = f"{base}/nft/v3/{self.ALCHEMY_API_KEY}"
    
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

DEFI_PROTOCOLS = {
    "aave_v3_pool": "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2",
    "aave_v2_lending": "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9",
    "compound_v3_usdc": "0xc3d688b66703497daa19211eedff47f25384cdc3",
    "compound_v2_comptroller": "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",
    "uniswap_v3_router": "0xe592427a0aece92de3edee1f18e0157c05861564",
    "uniswap_v2_router": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
    "curve_router": "0x99a58482bd75cbab83b27ec03ca68ff489b5788f",
}

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