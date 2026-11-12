import jwt
from typing import Annotated
from ..config.config import settings

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError

bearer = HTTPBearer()

def require_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
) -> dict:
    secret = settings.JWT_TOKEN
    if not secret:
        raise RuntimeError("JWT_TOKEN is not present")

    try:
        payload = jwt.decode(
            credentials.credentials,
            secret,
            algorithms=[settings.ALGORITHM],
            options={"require": ["sub", "exp"]}
        )

    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expire token",
            headers={"WWW-Authenticate": "Bearer"}
        ) from exc
    return payload