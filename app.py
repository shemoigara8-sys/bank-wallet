"""Bank Wallet Application - Main Entry Point"""
from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from routes.auth import auth_bp
from routes.wallet import wallet_bp
from routes.admin import admin_bp


def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(admin_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
