"""Application configuration"""
import os
from datetime import timedelta


class Config:
    """Base configuration"""
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kwallet-dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///kwallet.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    QR_FOLDER = os.path.join('static', 'qrcodes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Allowed file extensions for uploads
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
