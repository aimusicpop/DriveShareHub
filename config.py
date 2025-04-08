import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the application."""
    
    # Google API credentials
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    # Upload settings
    UPLOAD_FOLDER = '/tmp'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        # Documents
        'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
        # Images
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg',
        # Videos
        'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv',
        # Audio
        'mp3', 'wav', 'ogg', 'm4a', 'flac',
        # Archives
        'zip', 'rar', '7z', 'tar', 'gz'
    }
