from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/madavola"
    api_prefix: str = "/api/v1"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "madavola"
    access_token_exp_minutes: int = 60
    refresh_token_exp_days: int = 14
    document_storage_dir: str = "data/uploads"


settings = Settings()
