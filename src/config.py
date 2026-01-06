from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import List

class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    GEMINI_API_KEY: SecretStr | None = None
    OPENROUTER_API_KEY: SecretStr
    ADMIN_IDS: List[int]
    PROXY_URL: str | None = None

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

config = Settings()
