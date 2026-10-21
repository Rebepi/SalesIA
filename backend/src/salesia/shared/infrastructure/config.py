from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PRIVATE_STORAGE_PATH = BACKEND_ROOT / "private_storage"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    app_name: str = "SalesIA Enterprise"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:Rebepi8989@127.0.0.1:5432/salesia_enterprise"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_connect_timeout_seconds: int = Field(default=5, ge=1, le=60)
    database_pool_timeout_seconds: int = Field(default=10, ge=1, le=120)
    database_lock_timeout_seconds: int = Field(default=5, ge=1, le=120)
    database_statement_timeout_seconds: int = Field(default=60, ge=1, le=3600)
    database_idle_transaction_timeout_seconds: int = Field(default=120, ge=10, le=3600)
    app_database_user: str = "postgres"
    app_database_password: str = "Rebepi8989"

    secret_key: str = "salesia-enterprise-development-secret-key-min-32-chars-long"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://localhost:5234", "http://127.0.0.1:5234"]

    auth_encryption_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_starttls: bool = True
    report_delivery_allowed_domains: list[str] = []
    frontend_url: str = "http://localhost:5173"
    private_storage_path: str = str(DEFAULT_PRIVATE_STORAGE_PATH)
    backup_encryption_key: str = ""
    backup_database_url: str = ""
    source_revision: str = "development"
    attachment_max_bytes: int = 25_000_000
    availability_target: float = 0.999
    recovery_point_objective_minutes: int = 15
    recovery_time_objective_minutes: int = 120

    @model_validator(mode="after")
    def validate_production(self):
        storage_path = Path(self.private_storage_path).expanduser()
        if not storage_path.is_absolute():
            storage_path = BACKEND_ROOT / storage_path
        storage_path = storage_path.resolve()
        storage_path.mkdir(parents=True, exist_ok=True)
        self.private_storage_path = str(storage_path)
        if self.environment == "production":
            if not self.database_url.startswith("postgresql"):
                raise ValueError("Producción requiere PostgreSQL")
            if "development" in self.secret_key or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY debe ser un secreto de producción")
            if not self.auth_encryption_key:
                raise ValueError("AUTH_ENCRYPTION_KEY es obligatorio en producción")
            if not self.backup_encryption_key:
                raise ValueError("BACKUP_ENCRYPTION_KEY es obligatorio en producción")
            if not self.app_database_password:
                raise ValueError("APP_DATABASE_PASSWORD es obligatorio en producción")
        return self


settings = AppSettings()
