import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 0.5 * 1024 * 1024  # 0.5MB max file size
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'

    # LLM Configuration
    LLM_MODEL = "google/gemini-pro-1.5"
    LLM_API_KEY = os.environ.get('OPENROUTER_API_KEY')

    LLM_SYSTEM_PROMPT = """Help me translate the subtitle of a cooking course of mine into Vietnamese. Don't translate line by line or word by word; make sure take into account the context, what the speaker is trying to teach, what they're trying to convey, especially sentence they're talking at the time; then convert them into natural Vietnamese (how natives actually talk in the same context and style). When in doubt, choose options that are mostly related to the context. I'll provide a json content representing the subtitle, which contains the id of each item and its original content. Your ouput json should have same structure but with the translated content for each item instead. Don't keep original_content in your ouput json. Remember to break long lines into two approximately: not too abrupt, using the flow of the target language (Vietnamese), not using the original line breaks in the original language. It must start as [{"id"."""
    
    LLM_GENERATION_CONFIG = {
        "temperature": 0.9,
        "top_p": 0.8,
        "max_output_tokens": 2000,
        "response_mime_type": "application/json",
    }
    
    # Subtitle Processing
    SUBTITLE_CHUNK_SIZE = 40

    # Rate Limiting
    RATE_LIMIT = "10 per minute"
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_MAX_REQUESTS = 30