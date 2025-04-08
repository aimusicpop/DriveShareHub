import os
import tempfile
import logging
import youtube_dl

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service class for YouTube operations."""
    
    def __init__(self):
        """Initialize the YouTube service."""
        pass
    
    def download_video(self, youtube_url):
        """Download a video from YouTube.
        
        Args:
            youtube_url (str): YouTube video URL
            
        Returns:
            tuple: (file_path, filename, mime_type)
        """
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Configure youtube-dl options
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True
            }
            
            # Download the video
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                filename = ydl.prepare_filename(info_dict)
                title = info_dict.get('title', 'youtube_video')
                ext = info_dict.get('ext', 'mp4')
                
                # Get mime type based on extension
                if ext == 'mp4':
                    mime_type = 'video/mp4'
                elif ext == 'webm':
                    mime_type = 'video/webm'
                else:
                    mime_type = 'video/mp4'  # Default to mp4
                
                return filename, f"{title}.{ext}", mime_type
        except Exception as e:
            logger.error(f"Error downloading YouTube video: {str(e)}")
            raise Exception(f"Failed to download YouTube video: {str(e)}")
