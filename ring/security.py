from datetime import datetime, timedelta
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from jose import jwt, JWTError
from ring.config import get_config


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="internal/token")
password_hash = PasswordHash([BcryptHasher()])

ACCESS_TOKEN_TTL = 60 * 30  # 30 minutes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(
    data: dict[str, str | datetime], expires_ttl: int = ACCESS_TOKEN_TTL
) -> str:
    config = get_config()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_ttl)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        config.JWT_SIGNING_KEY,
        algorithm=config.JWT_SIGNING_ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            get_config().JWT_SIGNING_KEY,
            algorithms=[get_config().JWT_SIGNING_ALGORITHM],
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email
