from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    # Charger d'abord le .env racine (POSTGRES_*), puis services/api/.env
    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        extra="ignore",
    )

    app_env: str = "dev"
    database_url: str = ""
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = "madavola"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    api_prefix: str = "/api/v1"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "madavola"
    access_token_exp_minutes: int = 60
    refresh_token_exp_days: int = 14
    document_storage_dir: str = "data/uploads"
    webhook_shared_secret: str | None = None
    webhook_ip_allowlist: str | None = None
    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if self.database_url:
            return self
        if self.postgres_password:
            url = (
                f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
            object.__setattr__(self, "database_url", url)
        else:
            # Défaut Docker (compose définit DATABASE_URL)
            object.__setattr__(
                self,
                "database_url",
                "postgresql+psycopg://postgres:postgres@db:5432/madavola",
            )
        return self


settings = Settings()
