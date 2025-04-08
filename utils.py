import os
import tempfile
import logging
import mimetypes

logger = logging.getLogger(__name__)

def get_mime_type(filename):
    """Determine MIME type based on file extension.
    
    Args:
        filename (str): Name of the file
        
    Returns:
        str: MIME type
    """
    # Initialize mimetypes database
    mimetypes.init()
    
    # Get mime type based on file extension
    mime_type, _ = mimetypes.guess_type(filename)
    
    # Default to octet-stream if type couldn't be determined
    if mime_type is None:
        mime_type = 'application/octet-stream'
    
    return mime_type

def is_allowed_file(filename, allowed_extensions):
    """Check if a file is allowed based on its extension.
    
    Args:
        filename (str): Name of the file
        allowed_extensions (set): Set of allowed extensions
        
    Returns:
        bool: True if file is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def upload_from_youtube(youtube_url, drive_service, youtube_service):
    """Download a video from YouTube and upload it to Google Drive.
    
    Args:
        youtube_url (str): YouTube video URL
        drive_service (DriveService): Drive service instance
        youtube_service (YouTubeService): YouTube service instance
        
    Returns:
        str: ID of the uploaded file
    """
    try:
        # Download YouTube video
        file_path, filename, mime_type = youtube_service.download_video(youtube_url)
        
        # Upload to Google Drive
        with open(file_path, 'rb') as f:
            file_id = drive_service.upload_file(f, filename, mime_type)
        
        # Clean up temporary file
        os.unlink(file_path)
        
        return file_id
    except Exception as e:
        logger.error(f"Error uploading from YouTube: {str(e)}")
        # Clean up temporary file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.unlink(file_path)
        raise Exception(f"Failed to upload from YouTube: {str(e)}")
