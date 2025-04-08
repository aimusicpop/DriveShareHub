import os
import tempfile
import logging
import re
import youtube_dl

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service class for YouTube operations."""
    
    def __init__(self):
        """Initialize the YouTube service."""
        pass
    
    def _check_region_error(self, error_msg):
        """Check if the error is due to regional restrictions.
        
        Args:
            error_msg (str): Error message
            
        Returns:
            bool: True if it's a regional restriction error
        """
        region_patterns = [
            "not available in your country",
            "uploader has not made this video available in your country",
            "video is not available in your location",
            "This video is not available in your country"
        ]
        
        for pattern in region_patterns:
            if pattern.lower() in error_msg.lower():
                return True
        return False
    
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
            
            # Configure youtube-dl options with more verbosity for better error messages
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'quiet': False,  # Changed to False to get more detailed logs
                'no_warnings': False  # Changed to False to get more detailed warnings
            }
            
            # Extract video ID for better error messages
            video_id = None
            youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
            match = re.search(youtube_regex, youtube_url)
            if match:
                video_id = match.group(1)
            
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
        except youtube_dl.utils.DownloadError as e:
            error_msg = str(e)
            logger.error(f"YouTube download error: {error_msg}")
            
            if self._check_region_error(error_msg):
                # Provide a more helpful message for regional restrictions
                vid_info = f" (Video ID: {video_id})" if video_id else ""
                raise Exception(f"Video is not available in your region{vid_info}. Try a different video that doesn't have regional restrictions.")
            elif "Private video" in error_msg:
                raise Exception(f"This video is private and cannot be accessed. Please try a public video instead.")
            elif "This video has been removed" in error_msg:
                raise Exception(f"This video has been removed or deleted from YouTube. Please try another video.")
            else:
                raise Exception(f"Failed to download YouTube video: {error_msg}")
        except Exception as e:
            logger.error(f"Error downloading YouTube video: {str(e)}")
            raise Exception(f"Failed to download YouTube video: {str(e)}")
