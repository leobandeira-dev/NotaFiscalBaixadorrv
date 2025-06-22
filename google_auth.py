# Use this Flask blueprint for Google authentication. Do not use flask-dance.

import json
import os

import requests
from flask import Blueprint, redirect, request, url_for, current_app, flash
from flask_login import login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient
from datetime import datetime, timedelta

from models import User, db

GOOGLE_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

def get_redirect_url():
    """Get the appropriate redirect URL based on current domain"""
    # Check if we're on the custom domain
    if 'crossxml.com.br' in request.host:
        return f'https://crossxml.com.br/google_login/callback'
    # Default to Replit domain
    elif os.environ.get("REPLIT_DEV_DOMAIN"):
        return f'https://{os.environ["REPLIT_DEV_DOMAIN"]}/google_login/callback'
    else:
        # Fallback for local development
        return f'http://localhost:5000/google_login/callback'

# Display setup instructions to the user
replit_redirect = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "your-repl")}/google_login/callback'
custom_redirect = 'https://crossxml.com.br/google_login/callback'

print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add these URLs to Authorized redirect URIs:
   - {replit_redirect} (for Replit domain)
   - {custom_redirect} (for custom domain)

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

client = WebApplicationClient(GOOGLE_CLIENT_ID)

google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use dynamic redirect URL based on current domain
    redirect_uri = get_redirect_url()
    
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=redirect_uri,
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@google_auth.route("/google_login/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Use dynamic redirect URL based on current domain
    redirect_uri = get_redirect_url()
    
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace("http://", "https://"),
        redirect_url=redirect_uri,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    userinfo = userinfo_response.json()
    if userinfo.get("email_verified"):
        users_email = userinfo["email"]
        users_name = userinfo["given_name"]
        users_picture = userinfo.get("picture")
    else:
        return "User email not available or not verified by Google.", 400

    # Find or create user
    user = User.query.filter_by(email=users_email).first()
    if not user:
        # Create new user with trial period
        user = User()
        user.email = users_email
        user.name = users_name
        user.provider = 'google'
        user.trial_start_date = datetime.utcnow()
        user.trial_end_date = datetime.utcnow() + timedelta(days=7)
        user.is_trial_active = True
        user.profile_picture = users_picture
        user.active = True
        
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(f"New Google user created: {users_email}")
    else:
        # Update user info if needed
        if not user.name or user.name != users_name:
            user.name = users_name
        if users_picture and (not user.profile_picture or user.profile_picture != users_picture):
            user.profile_picture = users_picture
        db.session.commit()

    login_user(user)
    
    # Log activity
    from new_app import log_user_activity
    log_user_activity(user.id, 'login', f'Login via Google OAuth ({request.host})')

    return redirect(url_for("dashboard"))


@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))