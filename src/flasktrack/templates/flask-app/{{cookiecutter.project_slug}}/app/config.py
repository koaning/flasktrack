"""Application configuration."""

import os
from pathlib import Path

basedir = Path(__file__).parent.parent.absolute()


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "{{ cookiecutter.secret_key }}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Flask-Login settings
    REMEMBER_COOKIE_DURATION = 3600

    # Flask-Mail settings
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 1025))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() in [
        "true",
        "1",
        "yes",
    ]
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in [
        "true",
        "1",
        "yes",
    ]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "noreply@{{ cookiecutter.project_slug }}.local"
    )

    # Magic link settings
    MAGIC_LINK_EXPIRY_MINUTES = 15
    SHOW_MAGIC_LINK_IN_TERMINAL = False  # Override in development

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DEV_DATABASE_URL")
        or f"sqlite:///{basedir}/data/{{ cookiecutter.project_slug }}_dev.db"
    )


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("TEST_DATABASE_URL") or "sqlite:///:memory:"
    )


class ProductionConfig(Config):
    """Production configuration."""

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"sqlite:///{basedir}/data/{{ cookiecutter.project_slug }}.db"
    )

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler

        if not app.debug:
            syslog_handler = SysLogHandler()
            syslog_handler.setLevel(logging.WARNING)
            app.logger.addHandler(syslog_handler)


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
