"""Application configuration."""

import os
from pathlib import Path

basedir = Path(__file__).parent.parent.absolute()


class Config:
    """Base configuration."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'FcxvsrGrBgxFxohomSYppiOGNhzCahPp'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    
    # Flask-Login settings
    REMEMBER_COOKIE_DURATION = 3600
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f'sqlite:///{basedir}/data/haptik_dev.db'


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production configuration."""
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir}/data/haptik.db'
    
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
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}