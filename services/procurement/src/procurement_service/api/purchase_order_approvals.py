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
from procurement_service.services.purchase_order_approval_coordinator import (
    DuplicatePurchaseOrderApprovalError,
    PurchaseOrderApprovalCoordinator,
    PurchaseOrderApprovalCoordinatorError,
    PurchaseOrderApprovalNotFoundError,
    PurchaseOrderNotFoundError,
)


router = APIRouter(
    prefix="/purchase-orders",
    tags=["purchase-order-approvals"],
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
    "/{purchase_order_id}/submit-for-approval",
    response_model=ProcurementApprovalRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_purchase_order_for_approval(
    purchase_order_id: UUID,
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

    coordinator = PurchaseOrderApprovalCoordinator(session)

    try:
        _, approval = await coordinator.submit_for_approval(
            tenant_id=tenant_id,
            purchase_order_id=purchase_order_id,
            payload=payload,
        )
        await session.commit()

    except PurchaseOrderNotFoundError as exc:
        await session.rollback()
        raise not_found(exc) from exc

    except DuplicatePurchaseOrderApprovalError as exc:
        await session.rollback()
        raise conflict(exc) from exc

    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approval request already exists for purchase order",
        ) from exc

    except PurchaseOrderApprovalCoordinatorError as exc:
        await session.rollback()
        raise unprocessable(exc) from exc

    except Exception:
        await session.rollback()
        raise

    return approval


@router.post(
    "/{purchase_order_id}/approval-steps/{step_number}/approve",
    response_model=ProcurementApprovalRequestRead,
)
async def approve_purchase_order_step(
    purchase_order_id: UUID,
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

    coordinator = PurchaseOrderApprovalCoordinator(session)

    try:
        _, approval = await coordinator.approve_step(
            tenant_id=tenant_id,
            purchase_order_id=purchase_order_id,
            step_number=step_number,
            decision=payload,
        )
        await session.commit()

    except (
        PurchaseOrderNotFoundError,
        PurchaseOrderApprovalNotFoundError,
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

    except PurchaseOrderApprovalCoordinatorError as exc:
        await session.rollback()
        raise unprocessable(exc) from exc

    except Exception:
        await session.rollback()
        raise

    return approval


@router.post(
    "/{purchase_order_id}/approval-steps/{step_number}/reject",
    response_model=ProcurementApprovalRequestRead,
)
async def reject_purchase_order_step(
    purchase_order_id: UUID,
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

    coordinator = PurchaseOrderApprovalCoordinator(session)

    try:
        _, approval = await coordinator.reject_step(
            tenant_id=tenant_id,
            purchase_order_id=purchase_order_id,
            step_number=step_number,
            decision=payload,
        )
        await session.commit()

    except (
        PurchaseOrderNotFoundError,
        PurchaseOrderApprovalNotFoundError,
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

    except PurchaseOrderApprovalCoordinatorError as exc:
        await session.rollback()
        raise unprocessable(exc) from exc

    except Exception:
        await session.rollback()
        raise

    return approval
