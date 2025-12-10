import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # LangSmith / OpenAI
    OPENAI_API_KEY: str
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str = "ClaimsAgent"

    # Dataverse
    DATAVERSE_URL: str
    CLIENT_ID: str | None = None
    CLIENT_SECRET: str | None = None
    TENANT_ID: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
