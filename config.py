import os
import secrets
from datetime import timedelta


class Config:
    # Application Settings
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(16))
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Email configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

    # Base URL configuration
    if os.environ.get('RENDER_EXTERNAL_URL'):
        BASE_URL = os.environ.get('RENDER_EXTERNAL_URL')
    else:
        BASE_URL = "http://localhost:5000"

    # Database settings
    DATABASE_URI = os.getenv('DATABASE_PATH', 'rides.db')
