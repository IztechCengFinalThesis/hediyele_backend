from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.services.firebase import verify_token, signin_with_email_password

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