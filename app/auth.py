from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 scheme for token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ========== PASSWORD FUNCTIONS (FIXED) ==========

def hash_password(password: str) -> str:
    """Plain password → SHA256 → bcrypt hash"""
    # Truncate password to 72 bytes first (bcrypt limit)
    password_truncated = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    # Hash with bcrypt
    return pwd_context.hash(password_truncated)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    # Truncate password to 72 bytes first
    password_truncated = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    # Verify with bcrypt
    return pwd_context.verify(password_truncated, hashed_password)

# ========== JWT TOKEN FUNCTIONS ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> schemas.TokenData:
    """Verify JWT token and extract data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        return schemas.TokenData(username=username)
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# ========== USER AUTHENTICATION ==========

def authenticate_user(db: Session, username: str, password: str):
    """Check username and password"""
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    
    return user

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """Get current logged-in user from token"""
    token_data = verify_token(token)
    
    user = db.query(models.User).filter(
        models.User.username == token_data.username
    ).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user