from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Aplikace
    app_name: str = "Forms4SOC"
    app_version: str = "0.2.0"
    app_subtitle: str = "SOC Incident Management Portal"
    debug: bool = False

    # JWT
    jwt_secret_key: str = "change-me-in-production-use-strong-random-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hodin

    # Auth provider: "simple" | "oauth" | "ldap"
    auth_provider: str = "simple"

    # Počáteční admin účet (použit při prvním spuštění, pokud neexistuje žádný uživatel)
    admin_username: str = "admin"
    admin_password: str = "admin"

    # Cesty
    database_path: str = "data/forms4soc.db"

    # Výchozí adresáře (lze přepsat v GUI Settings)
    default_incidents_dir: str = "data/events"
    default_templates_dir: str = "data/workbooks"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
