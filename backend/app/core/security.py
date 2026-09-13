"""Simple bearer-token auth dependency for protected routes."""
from fastapi import Header

from app.config import get_settings
from app.core.exceptions import UnauthorizedError

settings = get_settings()


async def verify_api_token(authorization: str | None = Header(default=None)) -> None:
    """
    Validates 'Authorization: Bearer <token>' header against API_AUTH_TOKEN.
    In production, swap this for Azure AD / OAuth2 (e.g. via azure-identity + MSAL).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.api_auth_token:
        raise UnauthorizedError("Invalid API token")
