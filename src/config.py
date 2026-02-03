from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    ENVIRONMENT: str

    ALCHEMY_API_KEY: str
    
    API_PORT: int
    CORS_ORIGINS: list[str] = ["*"]
    

settings = Settings()