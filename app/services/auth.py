# Handles jwt token verification and map uuid to user_id
import json
import os
import time
from dataclasses import dataclass

import httpx
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt.algorithms import ECAlgorithm


load_dotenv()


SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]

SUPABASE_JWKS_URL = os.getenv(
    "SUPABASE_JWKS_URL",
    f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json",
)

SUPABASE_JWT_ISSUER = os.getenv(
    "SUPABASE_JWT_ISSUER",
    f"{SUPABASE_URL}/auth/v1",
)

SUPABASE_JWT_AUDIENCE = os.getenv(
    "SUPABASE_JWT_AUDIENCE",
    "authenticated",
)


bearer_scheme = HTTPBearer(auto_error=False)

_jwks_cache: dict | None = None
_jwks_cached_at = 0.0
_jwks_cache_seconds = 600

_user_cache: dict[str, tuple[int, float]] = {}
_user_cache_seconds = 300


@dataclass(frozen=True)
class AuthClaims:
    auth_id: str
    email: str | None


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    auth_id: str
    email: str | None


async def get_jwks() -> dict:
    global _jwks_cache
    global _jwks_cached_at

    now = time.monotonic()

    if (
        _jwks_cache is not None
        and now - _jwks_cached_at < _jwks_cache_seconds
    ):
        return _jwks_cache

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(SUPABASE_JWKS_URL)

    response.raise_for_status()

    _jwks_cache = response.json()
    _jwks_cached_at = now

    return _jwks_cache#type: ignore


async def verify_token(token: str) -> AuthClaims:
    try:
        header = jwt.get_unverified_header(token)

        if header.get("alg") != "ES256":
            raise ValueError("Unsupported signing algorithm")

        jwks = await get_jwks()

        signing_jwk = next(
            (
                key
                for key in jwks["keys"]
                if key.get("kid") == header.get("kid")
            ),
            None,
        )

        if signing_jwk is None:
            raise ValueError("Signing key was not found")

        public_key = ECAlgorithm.from_jwk(
            json.dumps(signing_jwk)
        )

        claims = jwt.decode(
            token,
            public_key, #type: ignore
            algorithms=["ES256"],
            audience=SUPABASE_JWT_AUDIENCE,
            issuer=SUPABASE_JWT_ISSUER,
        )

        auth_id = claims.get("sub")

        if not auth_id:
            raise ValueError("Token has no subject")

        return AuthClaims(
            auth_id=auth_id,
            email=claims.get("email"),
        )

    except (
        KeyError,
        ValueError,
        jwt.PyJWTError,
        httpx.HTTPError,
    ) as error:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
        ) from error


async def get_current_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> AuthClaims:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
        )

    return await verify_token(credentials.credentials)


def admin_headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_SECRET_KEY,
        "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
        "Content-Type": "application/json",
    }


async def find_or_create_user(
    auth: AuthClaims,
) -> int:
    cached = _user_cache.get(auth.auth_id)
    now = time.monotonic()

    if cached and now - cached[1] < _user_cache_seconds:
        return cached[0]

    params = {
        "select": "id",
        "auth_id": f"eq.{auth.auth_id}",
        "limit": "1",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        lookup = await client.get(
            f"{SUPABASE_URL}/rest/v1/users",
            params=params,
            headers=admin_headers(),
        )

        lookup.raise_for_status()
        rows = lookup.json()

        if rows:
            user_id = int(rows[0]["id"])
        else:
            created = await client.post(
                f"{SUPABASE_URL}/rest/v1/users",
                headers={
                    **admin_headers(),
                    "Prefer": "return=representation",
                },
                json={
                    "auth_id": auth.auth_id,
                },
            )

            created.raise_for_status()
            user_id = int(created.json()[0]["id"])

    _user_cache[auth.auth_id] = (user_id, now)

    return user_id


async def get_current_user(
    auth: AuthClaims = Depends(get_current_auth),
) -> AuthenticatedUser:
    user_id = await find_or_create_user(auth)

    return AuthenticatedUser(
        user_id=user_id,
        auth_id=auth.auth_id,
        email=auth.email,
    )