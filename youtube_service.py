import os
import tempfile
import logging
import re
import subprocess
import json
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service class for YouTube operations."""
    
    def __init__(self):
        """Initialize the YouTube service."""
        pass
    
    def _extract_video_id(self, youtube_url):
        """Extract video ID from YouTube URL.
        
        Args:
            youtube_url (str): YouTube video URL
            
        Returns:
            str: YouTube video ID or None
        """
        # Handle youtube.com URLs
        parsed_url = urlparse(youtube_url)
        if 'youtube.com' in parsed_url.netloc:
            if '/watch' in parsed_url.path:
                query = parse_qs(parsed_url.query)
                if 'v' in query:
                    return query['v'][0]
            elif '/embed/' in parsed_url.path or '/v/' in parsed_url.path:
                path_parts = parsed_url.path.split('/')
                return path_parts[-1]
        # Handle youtu.be URLs
        elif 'youtu.be' in parsed_url.netloc:
            path_parts = parsed_url.path.split('/')
            return path_parts[-1]
        
        # Try regex as fallback
        youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(youtube_regex, youtube_url)
        if match:
            return match.group(1)
            
        return None
    
    def _format_error_message(self, error_msg, video_id=None):
        """Format error message to be more user-friendly.
        
        Args:
            error_msg (str): Error message from youtube-dl
            video_id (str, optional): Video ID
            
        Returns:
            str: Formatted error message
        """
        vid_info = f" (Video ID: {video_id})" if video_id else ""
        
        # Regional restriction errors
        region_patterns = [
            "not available in your country",
            "uploader has not made this video available in your country",
            "video is not available in your location",
            "This video is not available in your country"
        ]
        for pattern in region_patterns:
            if pattern.lower() in error_msg.lower():
                return f"Video is not available in your region{vid_info}. Try a different video that doesn't have regional restrictions."
        
        # Private video errors
        if "Private video" in error_msg:
            return f"This video is private{vid_info} and cannot be accessed. Please try a public video instead."
        
        # Removed video errors
        if "This video has been removed" in error_msg:
            return f"This video has been removed or deleted from YouTube{vid_info}. Please try another video."
        
        # YouTube extractor errors
        if "Unable to extract" in error_msg:
            return f"Unable to process this YouTube video{vid_info}. This might be due to YouTube changing their site. Please try another video or try again later."
        
        # Fallback error message
        return f"Failed to download YouTube video{vid_info}: {error_msg}"
    
    def download_video(self, youtube_url):
        """Download a video from YouTube.
        
        Args:
            youtube_url (str): YouTube video URL
            
        Returns:
            tuple: (file_path, filename, mime_type)
        """
        video_id = None  # Initialize here to avoid undefined variable error
        temp_dir = None
        
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                raise Exception("Could not extract YouTube video ID from URL")
                
            output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            # First try to get info without downloading to check availability
            logger.info(f"Checking YouTube video: {youtube_url}")
            
            # Run command with python-subprocess instead of using youtube_dl directly
            # This gives us more control and helps isolate issues
            cmd = [
                'youtube-dl', 
                '--no-playlist',
                '--dump-json',
                youtube_url
            ]
            
            try:
                # Get video info to check if downloadable
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                # If we get here, the video info was successfully extracted
                video_info = json.loads(result.stdout)
                title = video_info.get('title', 'youtube_video')
                
                # Now download the actual video
                download_cmd = [
                    'youtube-dl',
                    '--no-playlist',
                    '-f', 'best',  # Get best quality
                    '-o', output_template,
                    youtube_url
                ]
                
                logger.info(f"Downloading video: {title}")
                download_result = subprocess.run(
                    download_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Get the output filename
                # This is a bit tricky as youtube-dl might change the extension
                files = os.listdir(temp_dir)
                if not files:
                    raise Exception("Download completed but no file was created.")
                
                downloaded_file = os.path.join(temp_dir, files[0])
                file_extension = os.path.splitext(downloaded_file)[1][1:]  # Remove the dot
                
                # Get mime type based on extension
                mime_type = 'video/mp4'  # Default
                if file_extension == 'mp4':
                    mime_type = 'video/mp4'
                elif file_extension == 'webm':
                    mime_type = 'video/webm'
                elif file_extension == 'mkv':
                    mime_type = 'video/x-matroska'
                elif file_extension in ['m4a', 'mp3', 'ogg', 'wav']:
                    mime_type = f'audio/{file_extension}'
                
                return downloaded_file, f"{title}.{file_extension}", mime_type
                
            except subprocess.CalledProcessError as e:
                error_output = e.stderr
                logger.error(f"YouTube download subprocess error: {error_output}")
                raise Exception(self._format_error_message(error_output, video_id))
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error downloading YouTube video: {error_msg}")
            
            # Clean up temporary directory if it exists
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
            # Get video_id if not defined yet or empty (might happen if error occurs before extraction)
            if video_id is None or not video_id:
                video_id = self._extract_video_id(youtube_url)
            
            # If the error is already formatted, just pass it through
            if "Try a different video" in error_msg or "Please try another video" in error_msg:
                raise Exception(error_msg)
            else:
                raise Exception(self._format_error_message(error_msg, video_id))
