import os
from flask import Flask
import logging
from logging.handlers import RotatingFileHandler

from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    from .utils.helpers import datetimeformat
    app.jinja_env.filters['datetimeformat'] = datetimeformat

    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.courses import course_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(admin_bp)

    return app
