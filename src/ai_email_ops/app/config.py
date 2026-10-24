from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    ollama_base_url: str
    llm_model: str
    embed_model: str
    secret_key: str
    access_token_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()