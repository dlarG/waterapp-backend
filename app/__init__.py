from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Initialize config
    config = Config()
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Import models here to ensure they're registered
    from app import models
    
    # Register blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    return app