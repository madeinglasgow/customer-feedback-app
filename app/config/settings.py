"""Application configuration.

Values are read from the environment with development-friendly defaults.
See .env.example at the project root for documentation of each variable.
"""

import os


def env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///feedback.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_ENV = os.environ.get("APP_ENV", "development")

    # Notification behavior. NOTIFICATION_MIN_URGENCY is the minimum urgency an
    # escalated item must reach before an immediate alert goes to the support team.
    NOTIFICATIONS_ENABLED = env_bool("NOTIFICATIONS_ENABLED", True)
    SUPPORT_TEAM_ID = os.environ.get("SUPPORT_TEAM_ID", "cs-team-inbox")
    NOTIFICATION_MIN_URGENCY = os.environ.get("NOTIFICATION_MIN_URGENCY", "high")

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "logs/app.log")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    NOTIFICATIONS_ENABLED = True
    NOTIFICATION_MIN_URGENCY = "high"
    LOG_FILE = None


class ProductionConfig(BaseConfig):
    DEBUG = False


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str | None = None) -> type[BaseConfig]:
    name = env_name or os.environ.get("APP_ENV", "development")
    try:
        return _CONFIGS[name]
    except KeyError:
        raise ValueError(f"Unknown APP_ENV: {name!r}") from None
