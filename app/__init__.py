from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import os

limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config, dry_run=False):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['DRY_RUN'] = dry_run

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    limiter.init_app(app)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app