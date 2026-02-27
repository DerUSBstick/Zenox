from __future__ import annotations
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

type EnvType = Literal["dev", "test", "prod"]

# In Docker Swarm, secrets are mounted at /run/secrets.
# When that directory exists we read secrets from files there;
# in local development we fall back to the .env file.
_SECRETS_DIR = Path("/run/secrets")
_USE_SECRETS = _SECRETS_DIR.is_dir()

class Config(BaseSettings):
    # Discord
    discord_token: str = Field(validation_alias="bot_token")
    discord_dev_guild_id: int

    # Sentry DSN
    sentry_dsn: str

    # API Keys
    youtube_api_key: str
    seeleland_api_url: str

    # Twitch API Credentials
    twitch_client_id: str
    twitch_client_secret: str

    # Misc
    env: EnvType = "dev"
    db_url: str
    webhook_url: str = Field(validation_alias="discord_webhook")

    # Command-line arguments
    schedule: bool = False

    model_config = SettingsConfigDict(
        env_file=None if _USE_SECRETS else ".env",
        env_file_encoding="utf-8",
        secrets_dir=str(_SECRETS_DIR) if _USE_SECRETS else None,
        cli_parse_args=True,
        cli_implicit_flags=True,
    )

    @property
    def cli_args(self) -> dict[str, Any]:
        return {
            "schedule": self.schedule,
        }

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"

# Only load .env manually in local development (not needed in Docker)
if not _USE_SECRETS:
    load_dotenv()

CONFIG = Config() # pyright: ignore[reportCallIssue]
print(f"CLI args: {CONFIG.cli_args}")
