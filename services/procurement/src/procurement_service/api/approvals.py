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
from procurement_service.repositories.approval import (
    ProcurementApprovalRepository,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCancel,
    ProcurementApprovalRequestCreate,
    ProcurementApprovalRequestRead,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.approval import (
    ApprovalRequestTerminalError,
    ApprovalStepDecisionError,
    ApprovalStepOrderError,
    ApprovalWorkflowService,
)


router = APIRouter(
    prefix="/approvals",
    tags=["approvals"],
)


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Approval request not found",
    )


def _workflow_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ApprovalRequestTerminalError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(
        exc,
        (ApprovalStepOrderError, ApprovalStepDecisionError),
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


@router.post(
    "",
    response_model=ProcurementApprovalRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_approval_request(
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

    repository = ProcurementApprovalRepository(session)

    existing = await repository.get_by_object(
        tenant_id=tenant_id,
        object_type=payload.object_type,
        object_id=payload.object_id,
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approval request already exists for object",
        )

    approval_request = ApprovalWorkflowService.create_request(
        tenant_id=tenant_id,
        payload=payload,
    )

    try:
        await repository.add(approval_request)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approval request already exists for object",
        ) from exc

    result = await repository.get_by_id(
        tenant_id=tenant_id,
        request_id=approval_request.id,
    )

    if result is None:
        raise _not_found()

    return result


@router.get(
    "/{request_id}",
    response_model=ProcurementApprovalRequestRead,
)
async def get_approval_request(
    request_id: UUID,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("procurement.approvals.read")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    del identity

    repository = ProcurementApprovalRepository(session)

    approval_request = await repository.get_by_id(
        tenant_id=tenant_id,
        request_id=request_id,
    )

    if approval_request is None:
        raise _not_found()

    return approval_request


@router.post(
    "/{request_id}/steps/{step_number}/approve",
    response_model=ProcurementApprovalRequestRead,
)
async def approve_step(
    request_id: UUID,
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

    repository = ProcurementApprovalRepository(session)

    try:
        approval_request = await repository.get_by_id(
            tenant_id=tenant_id,
            request_id=request_id,
            for_update=True,
        )

        if approval_request is None:
            raise _not_found()

        ApprovalWorkflowService.approve_step(
            request=approval_request,
            step_number=step_number,
            decision=payload,
        )

        await repository.flush()
        await session.commit()

    except HTTPException:
        await session.rollback()
        raise
    except (
        ApprovalRequestTerminalError,
        ApprovalStepOrderError,
        ApprovalStepDecisionError,
    ) as exc:
        await session.rollback()
        raise _workflow_error(exc) from exc
    except Exception:
        await session.rollback()
        raise

    result = await repository.get_by_id(
        tenant_id=tenant_id,
        request_id=request_id,
    )

    if result is None:
        raise _not_found()

    return result


@router.post(
    "/{request_id}/steps/{step_number}/reject",
    response_model=ProcurementApprovalRequestRead,
)
async def reject_step(
    request_id: UUID,
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

    repository = ProcurementApprovalRepository(session)

    try:
        approval_request = await repository.get_by_id(
            tenant_id=tenant_id,
            request_id=request_id,
            for_update=True,
        )

        if approval_request is None:
            raise _not_found()

        ApprovalWorkflowService.reject_step(
            request=approval_request,
            step_number=step_number,
            decision=payload,
        )

        await repository.flush()
        await session.commit()

    except HTTPException:
        await session.rollback()
        raise
    except (
        ApprovalRequestTerminalError,
        ApprovalStepOrderError,
        ApprovalStepDecisionError,
    ) as exc:
        await session.rollback()
        raise _workflow_error(exc) from exc
    except Exception:
        await session.rollback()
        raise

    result = await repository.get_by_id(
        tenant_id=tenant_id,
        request_id=request_id,
    )

    if result is None:
        raise _not_found()

    return result


@router.post(
    "/{request_id}/cancel",
    response_model=ProcurementApprovalRequestRead,
)
async def cancel_approval_request(
    request_id: UUID,
    payload: ProcurementApprovalRequestCancel,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("procurement.approvals.cancel")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    del identity

    repository = ProcurementApprovalRepository(session)

    try:
        approval_request = await repository.get_by_id(
            tenant_id=tenant_id,
            request_id=request_id,
            for_update=True,
        )

        if approval_request is None:
            raise _not_found()

        ApprovalWorkflowService.cancel_request(
            request=approval_request,
            comments=payload.comments,
        )

        await repository.flush()
        await session.commit()

    except HTTPException:
        await session.rollback()
        raise
    except ApprovalRequestTerminalError as exc:
        await session.rollback()
        raise _workflow_error(exc) from exc
    except Exception:
        await session.rollback()
        raise

    result = await repository.get_by_id(
        tenant_id=tenant_id,
        request_id=request_id,
    )

    if result is None:
        raise _not_found()

    return result
