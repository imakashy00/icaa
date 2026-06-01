from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str 



settings = Settings()  # type: ignore