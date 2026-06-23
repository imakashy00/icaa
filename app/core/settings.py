from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    DATABASE_URL: str
    embedding_model:str
    top_k_clauses:int = 3
    # Automatically look for a local .env file
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
