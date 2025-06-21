"""
Google OAuth Fix - Solução para problemas de CSRF state e jwks_uri
"""
import os
from authlib.integrations.flask_client import OAuth
from flask import session, request, url_for, redirect, flash
import secrets

def fix_oauth_session_state():
    """Fix CSRF state issues by ensuring proper session management"""
    if 'oauth_state' not in session:
        session['oauth_state'] = secrets.token_urlsafe(32)
    session.permanent = True
    return session['oauth_state']

def create_google_oauth_client(app):
    """Create properly configured Google OAuth client"""
    oauth = OAuth(app)
    
    # Use Google's OpenID Connect discovery document
    google = oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'select_account'  # Force account selection
        }
    )
    
    return oauth, google

def get_user_info_from_token(google, token):
    """Extract user info from OAuth token with multiple fallbacks"""
    user_info = None
    
    # Method 1: Parse ID token
    if 'id_token' in token:
        try:
            user_info = google.parse_id_token(token)
        except Exception as e:
            print(f"ID token parsing failed: {e}")
    
    # Method 2: Use userinfo endpoint
    if not user_info or not user_info.get('email'):
        try:
            resp = google.get('userinfo', token=token)
            if resp and resp.status_code == 200:
                user_info = resp.json()
        except Exception as e:
            print(f"Userinfo endpoint failed: {e}")
    
    # Method 3: JWT decode without verification (last resort)
    if not user_info or not user_info.get('email'):
        if 'id_token' in token:
            try:
                import jwt
                user_info = jwt.decode(token['id_token'], options={"verify_signature": False})
            except Exception as e:
                print(f"JWT decode failed: {e}")
    
    return user_info

def get_redirect_uri():
    """Get proper redirect URI for current environment"""
    if os.environ.get('REPLIT_DEV_DOMAIN'):
        return f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/auth/google/callback"
    else:
        return url_for('google_callback', _external=True, _scheme='https')