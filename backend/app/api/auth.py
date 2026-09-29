from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import hashlib
import secrets
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.database import get_db
from app.database.models import User
from app.schemas import Token, LoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
settings = get_settings()

DEMO_USERS = {
    "admin": {"password": "admin123", "role": "ADMIN", "full_name": "System Administrator"},
    "officer": {"password": "officer123", "role": "OFFICER", "full_name": "Project Officer"},
    "viewer": {"password": "viewer123", "role": "VIEWER", "full_name": "Analytics Viewer"},
}


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${h.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split("$", 1)
        check = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100000)
        return secrets.compare_digest(check.hex(), h)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.username == username).first()


def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_roles(*roles):
    def dep(user: User = Depends(require_user)) -> User:
        if user.role not in roles and user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dep


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username, "role": user.role})
    return Token(access_token=token, role=user.role, username=user.username)


@router.post("/login/json", response_model=Token)
def login_json(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username, "role": user.role})
    return Token(access_token=token, role=user.role, username=user.username)


@router.get("/me")
def me(user: User = Depends(require_user)):
    return {"username": user.username, "role": user.role, "full_name": user.full_name}
