import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt
from pymongo.collection import Collection

from backend.config.database import db
from backend.config.settings import (
    JWT_ACCESS_TOKEN_EXPIRE_DAYS,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from backend.models.user_model import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Base exception for authentication errors."""
    pass


class DuplicateEmailError(AuthError):
    """Raised when an email is already registered."""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when credentials do not match."""
    pass


class InvalidTokenError(AuthError):
    """Raised when a JWT token is invalid or expired."""
    pass


def get_users_collection() -> Collection:
    return db["users"]


def ensure_user_indexes() -> None:
    """Create unique indexes for the users collection."""
    try:
        users = get_users_collection()
        users.create_index("email", unique=True)
        logger.info("MongoDB users unique index verified")
    except Exception as exc:
        logger.warning("Could not create users index: %s", exc)


def hash_password(plain_password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        logger.error("Error verifying password: %s", exc)
        return False


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=JWT_ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise InvalidTokenError("Authentication token has expired. Please sign in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Invalid authentication token.") from exc


def _doc_to_user_response(doc: dict[str, Any]) -> UserResponse:
    """Convert MongoDB user doc to UserResponse model."""
    user_id = doc.get("user_id") or str(doc.get("_id"))
    created_at = doc.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at)
        except ValueError:
            created_at = datetime.now(timezone.utc)
    elif not isinstance(created_at, datetime):
        created_at = datetime.now(timezone.utc)

    return UserResponse(
        id=user_id,
        name=doc["name"],
        email=doc["email"],
        store_name=doc.get("store_name", f"{doc['name']}'s Store"),
        created_at=created_at,
    )


def register_user(payload: UserRegister) -> TokenResponse:
    """Register a new user in MongoDB and return authentication token."""
    users = get_users_collection()
    normalized_email = payload.email.lower()

    # Check if user already exists
    existing = users.find_one({"email": normalized_email})
    if existing:
        raise DuplicateEmailError("An account with this email address already exists.")

    hashed_pw = hash_password(payload.password)
    now = datetime.now(timezone.utc)
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    store_name = (payload.store_name or "").strip() or f"{payload.name}'s Store"

    user_doc = {
        "user_id": user_id,
        "name": payload.name.strip(),
        "email": normalized_email,
        "store_name": store_name,
        "hashed_password": hashed_pw,
        "created_at": now,
        "updated_at": now,
    }

    users.insert_one(user_doc)
    logger.info("Registered new user: %s (ID: %s)", normalized_email, user_id)

    user_response = _doc_to_user_response(user_doc)
    token = create_access_token({"sub": user_id, "email": normalized_email})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_response,
    )


def login_user(payload: UserLogin) -> TokenResponse:
    """Authenticate a user by email/username and password."""
    users = get_users_collection()
    login_id = payload.email.lower()

    # Match by email or username/name (case-insensitive)
    user_doc = users.find_one({
        "$or": [
            {"email": login_id},
            {"name": {"$regex": f"^{login_id}$", "$options": "i"}},
        ]
    })

    if not user_doc or not verify_password(payload.password, user_doc.get("hashed_password", "")):
        raise InvalidCredentialsError("Invalid email or password.")

    user_response = _doc_to_user_response(user_doc)
    token = create_access_token({"sub": user_response.id, "email": user_response.email})

    logger.info("User logged in successfully: %s", user_response.email)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_response,
    )


def get_current_user_from_token(token: str) -> UserResponse:
    """Retrieve and validate the user associated with a JWT token."""
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Malformed authentication token.")

    users = get_users_collection()
    user_doc = users.find_one({"user_id": user_id})
    if not user_doc:
        raise InvalidTokenError("User associated with this token does not exist.")

    return _doc_to_user_response(user_doc)
