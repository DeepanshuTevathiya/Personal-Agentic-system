import os
from uuid import UUID

import httpx
from fastapi import HTTPException

from app.services.auth import admin_headers


SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")


async def get_or_create_thread(
    user_id: int,
    thread_id: UUID | None,
) -> UUID:
    async with httpx.AsyncClient(timeout=10) as client:
        if thread_id is not None:
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/threads",
                params={
                    "select": "id",
                    "id": f"eq.{thread_id}",
                    "user_id": f"eq.{user_id}",
                    "limit": "1",
                },
                headers=admin_headers(),
            )

            response.raise_for_status()

            if not response.json():
                raise HTTPException(
                    status_code=404,
                    detail="Thread not found",
                )

            return thread_id

        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/threads",
            params={"select": "id"},
            headers={
                **admin_headers(),
                "Prefer": "return=representation",
            },
            json={"user_id": user_id},
        )

        response.raise_for_status()
        return UUID(response.json()[0]["id"])

async def list_user_threads(user_id: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/threads",
            params={
                "select": "id,title,created_at,updated_at",
                "user_id": f"eq.{user_id}",
                "order": "updated_at.desc",
            },
            headers=admin_headers(),
        )

        response.raise_for_status()
        return response.json()