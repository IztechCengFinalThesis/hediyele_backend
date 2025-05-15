import firebase_admin
from firebase_admin import credentials, auth
import os
import json
from pathlib import Path
import requests
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import base64

# Decode FIREBASE_ADMIN_JSON_BASE64 env variable and write firebase_admin.json if present
firebase_json_b64 = os.environ.get("FIREBASE_ADMIN_JSON_BASE64")
if firebase_json_b64:
    with open("firebase_admin.json", "wb") as f:
        f.write(base64.b64decode(firebase_json_b64))

# Get the absolute path to the Firebase credentials file
credentials_path = "firebase_admin.json"

# Initialize Firebase Admin SDK with credentials
cred = credentials.Certificate(credentials_path)
try:
    firebase_app = firebase_admin.initialize_app(cred)
except ValueError:
    # App already initialized
    firebase_app = firebase_admin.get_app()

# Firebase Auth REST API URLs
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts"
API_KEY = "AIzaSyD9r8TNUdBLWWVdvWtTKS-YJF7KEt7YaxE"  # This should be your Firebase Web API key

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates the token and returns the user information.
    """
    try:
        decoded_token = verify_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

class FirebaseAuth:
    """
    Firebase authentication dependency.
    Use this with Depends() to secure your endpoints.
    """
    def __init__(self):
        pass
        
    def __call__(self, request: Request, user = Depends(get_current_user)):
        # Add the user to the request state
        request.state.user = user
        return user

def verify_token(token):
    """
    Verify the Firebase token and return the decoded token if valid.
    Args:
        token (str): The Firebase token to verify
    Returns:
        dict: The decoded token if valid
    Raises:
        Exception: If the token is invalid or verification fails
    """
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(token, firebase_app)
        return decoded_token
    except Exception as e:
        # Invalid token
        raise Exception(f"Token verification failed: {str(e)}")

def signin_with_email_password(email, password):
    """
    Sign in with email and password using Firebase Auth REST API
    Args:
        email (str): User's email
        password (str): User's password
    Returns:
        dict: Response containing user info and tokens
    Raises:
        Exception: If authentication fails
    """
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    url = f"{FIREBASE_AUTH_URL}:signInWithPassword?key={API_KEY}"
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_message = "Authentication failed"
        try:
            error_data = response.json()
            if "error" in error_data and "message" in error_data["error"]:
                error_message = error_data["error"]["message"]
        except:
            pass
        raise Exception(f"Authentication failed: {error_message}")

def set_user_premium_status(uid: str, is_premium: bool = True):
    """
    Set custom claims for a user to mark them as premium.
    
    Args:
        uid (str): The Firebase user ID
        is_premium (bool): Whether the user should have premium status
        
    Returns:
        dict: Result message
        
    Raises:
        Exception: If setting custom claims fails
    """
    try:
        # Get current custom claims
        user = auth.get_user(uid)
        current_claims = user.custom_claims or {}
        
        # Update premium status
        current_claims['premium'] = is_premium
        
        # Set the custom claims
        auth.set_custom_user_claims(uid, current_claims)
        
        return {
            "status": "success",
            "message": f"Premium status updated to {is_premium} for user {uid}",
            "user_id": uid
        }
    except Exception as e:
        raise Exception(f"Failed to set premium status: {str(e)}")
    
def is_admin_user(user_info: dict) -> bool:
    """
    Check if user has admin access using Firebase custom claims.
    """
    return user_info.get("admin") == True

def is_premium_user(user_info: dict) -> bool:
    """
    Check if user has premium access using Firebase custom claims.
    """
    # First check custom claims from decoded token
    if user_info.get("premium") == True:
        return True
        
    # Then check if claim exists inside the 'claims' object
    claims = user_info.get("claims", {})
    if claims.get("premium") == True:
        return True
    
    # Backwards compatibility: email-based checks (for testing)
    premium_emails = ["premium@example.com", "admin@hediyele.com", "vip@hediyele.com"]
    
    # Check specific emails (temporary)
    if user_info.get("email") in premium_emails:
        # Auto-upgrade this user with custom claims for next time
        try:
            uid = user_info.get("uid")
            if uid:
                set_user_premium_status(uid, True)
        except:
            # Ignore any errors during auto-upgrade
            pass
        return True
    
    return False
class AdminAuth(FirebaseAuth):
    """
    Authentication dependency that also checks if the user is admin.
    """
    def __call__(self, request: Request, user = Depends(get_current_user)):
        user_info = super().__call__(request, user)
        if not is_admin_user(user_info):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for this endpoint",
            )
        return user_info

class PremiumAuth(FirebaseAuth):
    """
    Authentication dependency that also checks if the user is premium.
    """
    def __call__(self, request: Request, user = Depends(get_current_user)):
        # First, call the parent class to get and validate the user
        user_info = super().__call__(request, user)
        
        # Then check if the user is premium
        if not is_premium_user(user_info):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription required for this endpoint",
            )
            
        return user_info 