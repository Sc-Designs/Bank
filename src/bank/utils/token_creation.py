from datetime import timezone, datetime, timedelta
import jwt
from ..config.config import settings


def create_access_token(user_id: str) -> str:
    secret = settings.JWT_TOKEN
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    return jwt.encode(
        {"sub": user_id, "exp": expires},
        secret,
        algorithm=settings.ALGORITHM,
    )
