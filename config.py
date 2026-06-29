
import os


class Config:
    SECRET_KEY = "kwallet_secret_key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///kwallet.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join("static", "uploads")
    QR_FOLDER = os.path.join("static", "qrcodes")

