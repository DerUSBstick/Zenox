from __future__ import annotations
from dotenv import load_dotenv
from typing import Any, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

type EnvType = Literal["dev", "test", "prod"]

class Config(BaseSettings):
    # Discord
    discord_token: str = Field(validation_alias="bot_token")

    # Sentry DSN
    sentry_dsn: str

    # API Keys
    youtube_api_key: str
    seeleland_api_url: str

    # Misc
    env: EnvType = "dev"
    db_url: str
    webhook_url: str = Field(validation_alias="discord_webhook")

    # Command-line arguments
    schedule: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", cli_parse_args=True, cli_implicit_flags=True
    )

    @property
    def cli_args(self) -> dict[str, Any]:
        return {
            "schedule": self.schedule,
        }

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"

load_dotenv()

CONFIG = Config() # pyright: ignore[reportCallIssue]
print(f"CLI args: {CONFIG.cli_args}")