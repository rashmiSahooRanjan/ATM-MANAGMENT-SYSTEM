import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback_secret_key_change_me')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://rs5038676_db_user:JaM6PtuMSbV1hkJb@cluster0.oynmyxv.mongodb.net/atm_management')
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@1234')
