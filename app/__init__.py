from flask import Flask
from .extensions import db, migrate, cors
from config import Config
import os
import sys

def create_app(config_class=Config):
    # When frozen by PyInstaller, resolve template/static dirs to the bundle
    base_path = os.environ.get('TRIGEN_BASE_PATH', os.path.dirname(os.path.abspath(__file__)))
    if getattr(sys, 'frozen', False):
        template_dir = os.path.join(base_path, 'app', 'templates')
        static_dir = os.path.join(base_path, 'app', 'static')
        app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    else:
        app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Create necessary folders if they don't exist
    with app.app_context():
        folders = [
            app.config['UPLOAD_FOLDER'],
            os.path.join(os.path.dirname(app.config['UPLOAD_FOLDER']), 'reports'), 
            os.path.join(os.path.dirname(app.config['UPLOAD_FOLDER']), 'ml_models')
        ]
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # Preload ML models in the background
    import threading
    def preload_models():
        try:
            from app.services.ml_engine import MLEngine, _load_model
            _load_model('immunity_rf.joblib')
            _load_model('sickle_xgb.joblib')
            _load_model('lsd_gb.joblib')
        except Exception as e:
            print(f"[Init] Error preloading models: {e}")
            
    threading.Thread(target=preload_models, daemon=True).start()

    return app
