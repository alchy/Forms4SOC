from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Aplikace
    app_name: str = "Forms4SOC"
    app_version: str = "0.1.0"
    debug: bool = False

    # JWT
    jwt_secret_key: str = "change-me-in-production-use-strong-random-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hodin

    # Auth provider: "simple" | "oauth" | "ldap"
    auth_provider: str = "simple"

    # Jednoduchá autentizace (simple provider)
    admin_username: str = "admin"
    admin_password: str = "admin"

    # Cesty
    playbooks_dir: Path = Path("playbooks")
    database_path: Path = Path("data/forms4soc.db")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
