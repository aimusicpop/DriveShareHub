import os
import tempfile
import logging
import mimetypes
import requests
import cloudscraper
from urllib.parse import urlparse
from io import BytesIO

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

def download_with_cloudscraper(url, timeout=60):
    """Download a file using CloudScraper to bypass Cloudflare protection and CAPTCHA.
    
    Args:
        url (str): URL to download from
        timeout (int, optional): Timeout in seconds
        
    Returns:
        tuple: (filename, content, mime_type)
    """
    try:
        logger.info(f"Downloading from URL with CloudScraper: {url}")
        
        # Create a cloudscraper session with browser emulation
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=2  # Small delay to avoid triggering anti-bot measures
        )
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Perform the request with CloudScraper
        response = scraper.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        # Try to get filename from Content-Disposition header
        filename = None
        if 'Content-Disposition' in response.headers:
            import re
            content_disposition = response.headers['Content-Disposition']
            filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
            if filename_match:
                filename = filename_match.group(1)
        
        # If no filename in header, get it from URL
        if not filename:
            path = urlparse(url).path
            filename = os.path.basename(path)
            
        # If still no filename (empty path), use a default name
        if not filename or filename == '':
            filename = 'downloaded_file'
            
        # Determine MIME type from Content-Type header
        mime_type = response.headers.get('Content-Type', '').split(';')[0]
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type = get_mime_type(filename)
            
        # Ensure filename has an extension based on MIME type
        if '.' not in filename and mime_type != 'application/octet-stream':
            ext_map = {
                'application/pdf': '.pdf',
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'video/mp4': '.mp4',
                'audio/mpeg': '.mp3',
                'application/zip': '.zip'
            }
            if mime_type in ext_map:
                filename += ext_map[mime_type]
                    
        return filename, response.content, mime_type
    except Exception as e:
        logger.error(f"Error downloading with CloudScraper: {str(e)}")
        # Fall back to regular requests if CloudScraper fails
        try:
            logger.info(f"Falling back to regular requests: {url}")
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Get filename from URL
            filename = os.path.basename(urlparse(url).path)
            if not filename or filename == '':
                filename = 'downloaded_file'
                
            # Get mime type
            mime_type = response.headers.get('Content-Type', '').split(';')[0]
            if not mime_type or mime_type == 'application/octet-stream':
                mime_type = get_mime_type(filename)
                
            return filename, response.content, mime_type
        except Exception as fallback_error:
            logger.error(f"Error in request fallback: {str(fallback_error)}")
            raise Exception(f"Failed to download file: {str(e)}. Fallback also failed: {str(fallback_error)}")

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
