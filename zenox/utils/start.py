import sentry_sdk
from sentry_sdk.integrations.loguru import LoggingLevels, LoguruIntegration

from .misc import get_project_version
from zenox.config import CONFIG

__all__ = ("init_sentry",)


def init_sentry() -> None:
    sentry_sdk.init(
        dsn=CONFIG.sentry_dsn,
        integrations=[
            LoguruIntegration(
                level=LoggingLevels.INFO.value, event_level=LoggingLevels.ERROR.value
            ),
        ],
        traces_sample_rate=1.0,
        enable_tracing=True,
        profiles_sample_rate=1.0,
        environment=CONFIG.env,
        release=get_project_version(),
        send_default_pii=True,
    )
