from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """Model representing a user in the application."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    # Optional fields for Google OAuth tokens
    google_id = db.Column(db.String(64), unique=True)
    google_access_token = db.Column(db.String(255))
    google_refresh_token = db.Column(db.String(255))
    google_token_expiry = db.Column(db.DateTime)

    def __repr__(self):
        return f'<User {self.username}>'

class File:
    """Class representing a file stored in Google Drive."""
    
    def __init__(self, file_id, name, mime_type, created_time, size, web_view_link=None):
        """Initialize a new File object.
        
        Args:
            file_id (str): The Google Drive file ID
            name (str): The filename
            mime_type (str): The MIME type of the file
            created_time (str): When the file was created
            size (int): File size in bytes
            web_view_link (str, optional): Link to view the file
        """
        self.id = file_id
        self.name = name
        self.mime_type = mime_type
        self.created_time = created_time
        self.size = size
        self.web_view_link = web_view_link
    
    @property
    def file_type(self):
        """Get the general file type category based on MIME type."""
        if 'image/' in self.mime_type:
            return 'image'
        elif 'video/' in self.mime_type:
            return 'video'
        elif 'audio/' in self.mime_type:
            return 'audio'
        elif 'application/pdf' in self.mime_type:
            return 'pdf'
        elif 'application/vnd.google-apps.document' in self.mime_type:
            return 'document'
        elif 'application/vnd.google-apps.spreadsheet' in self.mime_type:
            return 'spreadsheet'
        elif 'application/vnd.google-apps.presentation' in self.mime_type:
            return 'presentation'
        elif any(archive in self.mime_type for archive in ['zip', 'x-rar', 'x-7z', 'x-tar', 'gzip']):
            return 'archive'
        else:
            return 'other'
    
    @property
    def formatted_size(self):
        """Return a human-readable file size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024.0:
                return f"{self.size:.2f} {unit}"
            self.size /= 1024.0
        return f"{self.size:.2f} TB"
    
    @property
    def formatted_date(self):
        """Return a formatted date string."""
        try:
            dt = datetime.fromisoformat(self.created_time.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return self.created_time
