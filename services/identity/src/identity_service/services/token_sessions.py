from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.core.tokens import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from identity_service.repositories.sessions import (
    create_user_session,
)
from identity_service.schemas.auth import TokenResponse


async def issue_token_pair_with_session(
    session: AsyncSession,
    *,
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str],
    expires_in: int,
    ip_address: str | None,
    user_agent: str | None,
    device_name: str | None = None,
) -> TokenResponse:
    access_token = create_access_token(
        subject=user_id,
        tenant_id=tenant_id,
        permissions=permissions,
    )

    refresh_token = create_refresh_token(
        subject=user_id,
        tenant_id=tenant_id,
    )

    refresh_payload = decode_token(
        refresh_token,
        expected_type=TokenType.REFRESH,
    )

    refresh_token_id = UUID(
        refresh_payload["jti"]
    )

    expires_at = datetime.fromtimestamp(
        refresh_payload["exp"],
        tz=UTC,
    )

    await create_user_session(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        refresh_token_id=refresh_token_id,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
        device_name=device_name,
    )

    await session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )
