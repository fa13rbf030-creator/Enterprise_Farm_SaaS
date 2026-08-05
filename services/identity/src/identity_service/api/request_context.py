from __future__ import annotations

from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        return forwarded.split(",", maxsplit=1)[0].strip()

    if request.client is None:
        return None

    return request.client.host


def get_user_agent(request: Request) -> str | None:
    return request.headers.get("User-Agent")
