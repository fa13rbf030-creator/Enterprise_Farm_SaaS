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
from procurement_service.services.requisition_approval_coordinator import (
    DuplicateRequisitionApprovalError,
    RequisitionApprovalCoordinator,
    RequisitionApprovalCoordinatorError,
    RequisitionApprovalNotFoundError,
    RequisitionNotFoundError,
)


router = APIRouter(
    prefix="/purchase-requisitions",
    tags=["purchase-requisition-approvals"],
)


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
    )


def _conflict(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(exc),
    )


def _unprocessable(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


@router.post(
    "/{requisition_id}/submit-for-approval",
    response_model=ProcurementApprovalRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_requisition_for_approval(
    requisition_id: UUID,
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

    coordinator = RequisitionApprovalCoordinator(session)

    try:
        _, approval = await coordinator.submit_for_approval(
            tenant_id=tenant_id,
            requisition_id=requisition_id,
            payload=payload,
        )
        await session.commit()

    except RequisitionNotFoundError as exc:
        await session.rollback()
        raise _not_found(exc) from exc

    except DuplicateRequisitionApprovalError as exc:
        await session.rollback()
        raise _conflict(exc) from exc

    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approval request already exists for requisition",
        ) from exc

    except RequisitionApprovalCoordinatorError as exc:
        await session.rollback()
        raise _unprocessable(exc) from exc

    except Exception:
        await session.rollback()
        raise

    return approval


@router.post(
    "/{requisition_id}/approval-steps/{step_number}/approve",
    response_model=ProcurementApprovalRequestRead,
)
async def approve_requisition_step(
    requisition_id: UUID,
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

    coordinator = RequisitionApprovalCoordinator(session)

    try:
        _, approval = await coordinator.approve_step(
            tenant_id=tenant_id,
            requisition_id=requisition_id,
            step_number=step_number,
            decision=payload,
        )
        await session.commit()

    except (
        RequisitionNotFoundError,
        RequisitionApprovalNotFoundError,
    ) as exc:
        await session.rollback()
        raise _not_found(exc) from exc

    except (
        ApprovalRequestTerminalError,
        ApprovalStepOrderError,
        ApprovalStepDecisionError,
    ) as exc:
        await session.rollback()
        raise _conflict(exc) from exc

    except RequisitionApprovalCoordinatorError as exc:
        await session.rollback()
        raise _unprocessable(exc) from exc

    except Exception:
        await session.rollback()
        raise

    return approval


@router.post(
    "/{requisition_id}/approval-steps/{step_number}/reject",
    response_model=ProcurementApprovalRequestRead,
)
async def reject_requisition_step(
    requisition_id: UUID,
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

    coordinator = RequisitionApprovalCoordinator(session)

    try:
        _, approval = await coordinator.reject_step(
            tenant_id=tenant_id,
            requisition_id=requisition_id,
            step_number=step_number,
            decision=payload,
        )
        await session.commit()

    except (
        RequisitionNotFoundError,
        RequisitionApprovalNotFoundError,
    ) as exc:
        await session.rollback()
        raise _not_found(exc) from exc

    except (
        ApprovalRequestTerminalError,
        ApprovalStepOrderError,
        ApprovalStepDecisionError,
    ) as exc:
        await session.rollback()
        raise _conflict(exc) from exc

    except RequisitionApprovalCoordinatorError as exc:
        await session.rollback()
        raise _unprocessable(exc) from exc

    except Exception:
        await session.rollback()
        raise

    return approval
