from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    JournalSource,
    JournalStatus,
)
from finance_service.db.session import get_db_session
from finance_service.schemas.inquiry import (
    JournalSearchItem,
    LedgerInquiryRead,
)
from finance_service.services.inquiry import (
    InquiryValidationError,
    build_journal_search,
    build_ledger_inquiry,
)


router = APIRouter(
    prefix="/gl",
    tags=["general-ledger-inquiry"],
)


@router.get(
    "/accounts/{ledger_account_id}/inquiry",
    response_model=LedgerInquiryRead,
)
async def get_ledger_inquiry(
    ledger_account_id: UUID,
    fiscal_period_id: UUID = Query(...),
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> LedgerInquiryRead:
    try:
        return await build_ledger_inquiry(
            session,
            tenant_id=x_tenant_id,
            ledger_account_id=ledger_account_id,
            fiscal_period_id=fiscal_period_id,
        )
    except InquiryValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/journals",
    response_model=list[JournalSearchItem],
)
async def get_journal_search(
    fiscal_period_id: UUID | None = None,
    journal_status: JournalStatus | None = Query(
        default=None,
        alias="status",
    ),
    source: JournalSource | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    journal_number: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> list[JournalSearchItem]:
    try:
        return await build_journal_search(
            session,
            tenant_id=x_tenant_id,
            fiscal_period_id=fiscal_period_id,
            status=journal_status,
            source=source,
            date_from=date_from,
            date_to=date_to,
            journal_number=journal_number,
            limit=limit,
        )
    except InquiryValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
