import json
import os
import requests
from flask import Blueprint, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from oauthlib.oauth2 import WebApplicationClient

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# OAuth client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Create blueprint
google_auth = Blueprint("google_auth", __name__)

@google_auth.route("/google_login")
def login():
    """Initiate Google OAuth login flow."""
    # Find out what URL to hit for Google login
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        # Replace http with https for the external domain
        redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
        scope=["openid", "email", "profile", "https://www.googleapis.com/auth/drive"],
    )
    return redirect(request_uri)

@google_auth.route("/google_login/callback")
def callback():
    """Handle Google OAuth callback after user authorizes."""
    # Import here to avoid circular imports
    from app import db
    from models import User
    
    # Get authorization code Google sent back
    code = request.args.get("code")
    
    # Find out what URL to hit to get tokens
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Prepare and send a request to get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace("http://", "https://"),
        redirect_url=request.base_url.replace("http://", "https://"),
        code=code
    )
    
    # Make sure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are not None before using as auth
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET else None
    )

    # Parse the tokens
    client.parse_request_body_response(json.dumps(token_response.json()))
    
    # Get user info from Google
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    
    # Make sure the email is verified
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json().get("given_name", users_email.split('@')[0])
        
        # Get tokens for Drive API access
        tokens = token_response.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        
        # Check if user exists; if not, create a new user
        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User(
                username=users_name,
                email=users_email,
                google_id=unique_id,
                google_access_token=access_token,
                google_refresh_token=refresh_token
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update existing user's tokens
            user.google_id = unique_id
            user.google_access_token = access_token
            if refresh_token:  # Not always returned on subsequent logins
                user.google_refresh_token = refresh_token
            db.session.commit()
            
        # Begin user session
        login_user(user)
        
        # Redirect to homepage or next page
        flash(f"Welcome, {users_name}! You are now logged in with Google.", "success")
        return redirect(url_for("index"))
    else:
        flash("User email not available or not verified by Google.", "danger")
        return redirect(url_for("index"))

@google_auth.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))