from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from procurement_service.api.security import (
    CurrentIdentity,
    enforce_tenant_header,
    require_permission,
)
from procurement_service.db.session import get_db_session
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalRequestRead,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.approval import (
    ApprovalRequestTerminalError,
    ApprovalStepDecisionError,
    ApprovalStepOrderError,
)
from procurement_service.services.invoice_match_approval import (
    InvalidInvoiceMatchTransitionError,
)
from procurement_service.services.invoice_match_approval_coordinator import (
    DuplicateInvoiceMatchApprovalError,
    InvoiceMatchApprovalCoordinator,
    InvoiceMatchApprovalCoordinatorError,
    InvoiceMatchApprovalNotFoundError,
    InvoiceMatchNotFoundError,
)

router = APIRouter(
    prefix="/invoice-matches",
    tags=["invoice-match-approvals"],
)


def not_found(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
    )


def conflict(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(exc),
    )


def unprocessable(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


@router.post(
    "/{invoice_match_id}/submit-for-approval",
    response_model=ProcurementApprovalRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_invoice_match_for_approval(
    invoice_match_id: UUID,
    payload: ProcurementApprovalRequestCreate,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("procurement.approvals.create")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    if (
        payload.requested_by != identity.user_id
        and not identity.has_ceo_override
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="requested_by must match authenticated user",
        )

    coordinator = InvoiceMatchApprovalCoordinator(session)

    try:
        _, approval = await coordinator.submit_for_approval(
            tenant_id=tenant_id,
            invoice_match_id=invoice_match_id,
            payload=payload,
        )
        await session.commit()

    except InvoiceMatchNotFoundError as exc:
        await session.rollback()
        raise not_found(exc) from exc

    except DuplicateInvoiceMatchApprovalError as exc:
        await session.rollback()
        raise conflict(exc) from exc

    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Approval request already exists "
                "for invoice match"
            ),
        ) from exc

    except (
        InvoiceMatchApprovalCoordinatorError,
        InvalidInvoiceMatchTransitionError,
    ) as exc:
        await session.rollback()
        raise unprocessable(exc) from exc

    except Exception:
        await session.rollback()
        raise

    return approval


@router.post(
    "/{invoice_match_id}/approval-steps/{step_number}/approve",
    response_model=ProcurementApprovalRequestRead,
)
async def approve_invoice_match_step(
    invoice_match_id: UUID,
    step_number: int,
    payload: ProcurementApprovalStepDecision,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("procurement.approvals.approve")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    if (
        payload.decided_by != identity.user_id
        and not identity.has_ceo_override
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="decided_by must match authenticated user",
        )

    coordinator = InvoiceMatchApprovalCoordinator(session)

    try:
        _, approval = await coordinator.approve_step(
            tenant_id=tenant_id,
            invoice_match_id=invoice_match_id,
            step_number=step_number,
            decision=payload,
        )
        await session.commit()

    except (
        InvoiceMatchNotFoundError,
        InvoiceMatchApprovalNotFoundError,
    ) as exc:
        await session.rollback()
        raise not_found(exc) from exc

    except (
        ApprovalRequestTerminalError,
        ApprovalStepOrderError,
        ApprovalStepDecisionError,
    ) as exc:
        await session.rollback()
        raise conflict(exc) from exc

    except (
        InvoiceMatchApprovalCoordinatorError,
        InvalidInvoiceMatchTransitionError,
    ) as exc:
        await session.rollback()
        raise unprocessable(exc) from exc

    except Exception:
        await session.rollback()
        raise

    return approval


@router.post(
    "/{invoice_match_id}/approval-steps/{step_number}/reject",
    response_model=ProcurementApprovalRequestRead,
)
async def reject_invoice_match_step(
    invoice_match_id: UUID,
    step_number: int,
    payload: ProcurementApprovalStepDecision,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("procurement.approvals.reject")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    if (
        payload.decided_by != identity.user_id
        and not identity.has_ceo_override
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="decided_by must match authenticated user",
        )

    coordinator = InvoiceMatchApprovalCoordinator(session)

    try:
        _, approval = await coordinator.reject_step(
            tenant_id=tenant_id,
            invoice_match_id=invoice_match_id,
            step_number=step_number,
            decision=payload,
        )
        await session.commit()

    except (
        InvoiceMatchNotFoundError,
        InvoiceMatchApprovalNotFoundError,
    ) as exc:
        await session.rollback()
        raise not_found(exc) from exc

    except (
        ApprovalRequestTerminalError,
        ApprovalStepOrderError,
        ApprovalStepDecisionError,
    ) as exc:
        await session.rollback()
        raise conflict(exc) from exc

    except (
        InvoiceMatchApprovalCoordinatorError,
        InvalidInvoiceMatchTransitionError,
    ) as exc:
        await session.rollback()
        raise unprocessable(exc) from exc

    except Exception:
        await session.rollback()
        raise

    return approval
