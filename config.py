import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 0.5 * 1024 * 1024  # 0.5MB max file size
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'