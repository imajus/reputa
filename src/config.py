from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    ENVIRONMENT: str

    ALCHEMY_API_KEY: str

    POAP_CONTRACT: str
    ENS_NAMEWRAPPER: str
    API_PORT: int

    @property
    def ALCHEMY_NFT_URL(self) -> str:
        return f"https://eth-mainnet.g.alchemy.com/nft/v3/{self.ALCHEMY_API_KEY}"

    @property
    def ALCHEMY_CORE_URL(self) -> str:
        return f"https://eth-mainnet.g.alchemy.com/v2/{self.ALCHEMY_API_KEY}"


settings = Settings()
