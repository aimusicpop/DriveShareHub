import os
import tempfile
import requests
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from io import BytesIO
from models import File

logger = logging.getLogger(__name__)

class DriveService:
    """Service class for Google Drive operations."""
    
    def __init__(self, api_key=None, client_id=None, client_secret=None, user_credentials=None):
        """Initialize the Drive service.
        
        Args:
            api_key (str, optional): Google API key
            client_id (str, optional): Google OAuth client ID
            client_secret (str, optional): Google OAuth client secret
            user_credentials (dict, optional): User's OAuth credentials with token and refresh_token
        """
        self.api_key = api_key or os.environ.get('GOOGLE_API_KEY')
        self.client_id = client_id or os.environ.get('GOOGLE_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('GOOGLE_CLIENT_SECRET')
        self.user_credentials = user_credentials
        self.service = self._build_service()
    
    def _build_service(self):
        """Build and return a Drive service object."""
        try:
            # If user OAuth credentials are available, use them
            if self.user_credentials and self.user_credentials.get('token'):
                creds = Credentials(
                    token=self.user_credentials.get('token'),
                    refresh_token=self.user_credentials.get('refresh_token'),
                    client_id=os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
                    client_secret=os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'),
                    token_uri='https://oauth2.googleapis.com/token',
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                service = build('drive', 'v3', credentials=creds)
                return service
            else:
                # Fall back to API key for limited access
                service = build('drive', 'v3', developerKey=self.api_key)
                return service
        except Exception as e:
            logger.error(f"Error building Drive service: {str(e)}")
            raise Exception(f"Failed to initialize Google Drive service: {str(e)}")
    
    def list_files(self, max_results=100):
        """List files in Google Drive.
        
        Args:
            max_results (int, optional): Maximum number of files to return
            
        Returns:
            list: List of File objects
        """
        try:
            results = self.service.files().list(
                pageSize=max_results,
                fields="files(id, name, mimeType, createdTime, size, webViewLink)"
            ).execute()
            
            items = results.get('files', [])
            files = []
            
            for item in items:
                file = File(
                    file_id=item.get('id', ''),
                    name=item.get('name', 'Unnamed'),
                    mime_type=item.get('mimeType', 'unknown/unknown'),
                    created_time=item.get('createdTime', ''),
                    size=int(item.get('size', 0)) if item.get('size') else 0,
                    web_view_link=item.get('webViewLink', '')
                )
                files.append(file)
            
            return files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise Exception(f"Failed to list files: {str(e)}")
    
    def upload_file(self, file_obj, filename, mime_type=None):
        """Upload a file to Google Drive.
        
        Args:
            file_obj (FileStorage): File object to upload
            filename (str): Name of the file
            mime_type (str, optional): MIME type of the file
            
        Returns:
            str: ID of the uploaded file
        """
        try:
            # Save the file temporarily
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            file_obj.save(temp_file.name)
            temp_file.close()
            
            # Create file metadata
            file_metadata = {'name': filename}
            
            # Create media
            media = MediaFileUpload(
                temp_file.name,
                mimetype=mime_type,
                resumable=True
            )
            
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            # Clean up temporary file
            os.unlink(temp_file.name)
            
            return file.get('id')
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            # Clean up temporary file if it exists
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise Exception(f"Failed to upload file: {str(e)}")
    
    def upload_from_url(self, url):
        """Download a file from a URL and upload it to Google Drive.
        
        Args:
            url (str): URL to download from
            
        Returns:
            str: ID of the uploaded file
        """
        try:
            # Download file from URL
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Get filename from URL
            filename = url.split('/')[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
            
            # Determine content type
            content_type = response.headers.get('content-type', 'application/octet-stream')
            
            # Create file metadata
            file_metadata = {'name': filename}
            
            # Create media
            fh = BytesIO(response.content)
            media = MediaIoBaseUpload(
                fh,
                mimetype=content_type,
                resumable=True
            )
            
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
        except Exception as e:
            logger.error(f"Error uploading from URL: {str(e)}")
            raise Exception(f"Failed to upload from URL: {str(e)}")
    
    def delete_file(self, file_id):
        """Delete a file from Google Drive.
        
        Args:
            file_id (str): ID of the file to delete
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            raise Exception(f"Failed to delete file: {str(e)}")
