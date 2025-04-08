import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from config import Config
from drive_service import DriveService
from youtube_service import YouTubeService
import utils

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Initialize services
drive_service = None
youtube_service = None

# Routes
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Setup page for Google Drive API credentials."""
    global drive_service
    
    if request.method == 'POST':
        try:
            api_key = request.form.get('api_key')
            client_id = request.form.get('client_id')
            client_secret = request.form.get('client_secret')
            
            # Save credentials in session for this user
            session['api_key'] = api_key
            session['client_id'] = client_id
            session['client_secret'] = client_secret
            
            # Initialize drive service with these credentials
            drive_service = DriveService(api_key, client_id, client_secret)
            
            flash('Google Drive API credentials saved successfully!', 'success')
            return redirect(url_for('uploads'))
        except Exception as e:
            logger.error(f"Error in setup: {str(e)}")
            flash(f'Error setting up credentials: {str(e)}', 'danger')
    
    return render_template('setup.html')

@app.route('/uploads')
def uploads():
    """Render the uploads page."""
    # Check if credentials are set
    if not session.get('api_key') or not session.get('client_id') or not session.get('client_secret'):
        flash('Please set up your Google Drive API credentials first.', 'warning')
        return redirect(url_for('setup'))
    
    return render_template('uploads.html')

@app.route('/files')
def files():
    """View files in Google Drive."""
    global drive_service
    
    # Check if credentials are set
    if not session.get('api_key') or not session.get('client_id') or not session.get('client_secret'):
        flash('Please set up your Google Drive API credentials first.', 'warning')
        return redirect(url_for('setup'))
    
    try:
        if not drive_service:
            drive_service = DriveService(
                session.get('api_key'),
                session.get('client_id'),
                session.get('client_secret')
            )
        
        files_list = drive_service.list_files()
        return render_template('files.html', files=files_list)
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        flash(f'Error listing files: {str(e)}', 'danger')
        return render_template('files.html', files=[])

@app.route('/upload/file', methods=['POST'])
def upload_file():
    """Handle direct file upload."""
    global drive_service
    
    if not drive_service:
        drive_service = DriveService(
            session.get('api_key'),
            session.get('client_id'),
            session.get('client_secret')
        )
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Secure the filename and determine MIME type
        filename = secure_filename(file.filename)
        mime_type = utils.get_mime_type(filename)
        
        # Upload to Google Drive
        file_id = drive_service.upload_file(file, filename, mime_type)
        
        return jsonify({
            "success": True,
            "message": f"File {filename} uploaded successfully",
            "file_id": file_id
        })
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload/url', methods=['POST'])
def upload_from_url():
    """Handle upload from a direct URL."""
    global drive_service
    
    if not drive_service:
        drive_service = DriveService(
            session.get('api_key'),
            session.get('client_id'),
            session.get('client_secret')
        )
    
    try:
        url = request.form.get('url')
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Download from URL and upload to Drive
        file_id = drive_service.upload_from_url(url)
        
        return jsonify({
            "success": True,
            "message": "File uploaded from URL successfully",
            "file_id": file_id
        })
    except Exception as e:
        logger.error(f"Error uploading from URL: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload/youtube', methods=['POST'])
def upload_from_youtube():
    """Handle upload from a YouTube URL."""
    global drive_service, youtube_service
    
    if not drive_service:
        drive_service = DriveService(
            session.get('api_key'),
            session.get('client_id'),
            session.get('client_secret')
        )
    
    if not youtube_service:
        youtube_service = YouTubeService()
    
    try:
        youtube_url = request.form.get('youtube_url')
        if not youtube_url:
            return jsonify({"error": "No YouTube URL provided"}), 400
        
        # Download YouTube video and upload to Drive
        file_id = utils.upload_from_youtube(youtube_url, drive_service, youtube_service)
        
        return jsonify({
            "success": True,
            "message": "YouTube video uploaded successfully",
            "file_id": file_id
        })
    except Exception as e:
        logger.error(f"Error uploading from YouTube: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/file/delete/<file_id>', methods=['POST'])
def delete_file(file_id):
    """Delete a file from Google Drive."""
    global drive_service
    
    if not drive_service:
        drive_service = DriveService(
            session.get('api_key'),
            session.get('client_id'),
            session.get('client_secret')
        )
    
    try:
        drive_service.delete_file(file_id)
        flash('File deleted successfully!', 'success')
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        flash(f'Error deleting file: {str(e)}', 'danger')
    
    return redirect(url_for('files'))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(e)}")
    return render_template('index.html', error="Internal server error. Please try again later."), 500
