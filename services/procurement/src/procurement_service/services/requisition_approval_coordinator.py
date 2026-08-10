from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    PurchaseRequisition,
)
from procurement_service.repositories.approval import (
    ProcurementApprovalRepository,
)
from procurement_service.repositories.requisition import (
    PurchaseRequisitionRepository,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.approval import (
    ApprovalWorkflowService,
)
from procurement_service.services.requisition_approval import (
    RequisitionApprovalIntegrationService,
)


class RequisitionApprovalCoordinatorError(ValueError):
    """Base coordinator error."""


class RequisitionNotFoundError(
    RequisitionApprovalCoordinatorError
):
    """Raised when the requisition does not exist for the tenant."""


class DuplicateRequisitionApprovalError(
    RequisitionApprovalCoordinatorError
):
    """Raised when the requisition already has an approval request."""


class RequisitionApprovalNotFoundError(
    RequisitionApprovalCoordinatorError
):
    """Raised when the requisition approval request does not exist."""


class RequisitionApprovalCoordinator:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.requisitions = PurchaseRequisitionRepository(
            session
        )
        self.approvals = ProcurementApprovalRepository(
            session
        )

    async def submit_for_approval(
        self,
        *,
        tenant_id: UUID,
        requisition_id: UUID,
        payload: ProcurementApprovalRequestCreate,
    ) -> tuple[
        PurchaseRequisition,
        ProcurementApprovalRequest,
    ]:
        if (
            payload.object_type
            != ApprovalObjectType.PURCHASE_REQUISITION
        ):
            raise RequisitionApprovalCoordinatorError(
                "approval payload must target a purchase requisition"
            )

        if payload.object_id != requisition_id:
            raise RequisitionApprovalCoordinatorError(
                "approval payload object does not match requisition"
            )

        requisition = await self.requisitions.get_by_id(
            tenant_id=tenant_id,
            requisition_id=requisition_id,
            for_update=True,
        )

        if requisition is None:
            raise RequisitionNotFoundError(
                "purchase requisition not found"
            )

        existing = await self.approvals.get_by_object(
            tenant_id=tenant_id,
            object_type=ApprovalObjectType.PURCHASE_REQUISITION,
            object_id=requisition_id,
            for_update=True,
        )

        if existing is not None:
            raise DuplicateRequisitionApprovalError(
                "purchase requisition already has an approval request"
            )

        RequisitionApprovalIntegrationService.submit(
            requisition=requisition
        )

        approval = ApprovalWorkflowService.create_request(
            tenant_id=tenant_id,
            payload=payload,
        )

        await self.approvals.add(approval)
        await self.requisitions.flush()

        return requisition, approval

    async def approve_step(
        self,
        *,
        tenant_id: UUID,
        requisition_id: UUID,
        step_number: int,
        decision: ProcurementApprovalStepDecision,
    ) -> tuple[
        PurchaseRequisition,
        ProcurementApprovalRequest,
    ]:
        requisition, approval = (
            await self._load_for_decision(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
            )
        )

        ApprovalWorkflowService.approve_step(
            request=approval,
            step_number=step_number,
            decision=decision,
        )

        if approval.status == ApprovalRequestStatus.APPROVED:
            RequisitionApprovalIntegrationService.synchronize_terminal_approval(
                requisition=requisition,
                approval_request=approval,
                decided_by=decision.decided_by,
            )

        await self.approvals.flush()
        await self.requisitions.flush()

        return requisition, approval

    async def reject_step(
        self,
        *,
        tenant_id: UUID,
        requisition_id: UUID,
        step_number: int,
        decision: ProcurementApprovalStepDecision,
    ) -> tuple[
        PurchaseRequisition,
        ProcurementApprovalRequest,
    ]:
        requisition, approval = (
            await self._load_for_decision(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
            )
        )

        ApprovalWorkflowService.reject_step(
            request=approval,
            step_number=step_number,
            decision=decision,
        )

        RequisitionApprovalIntegrationService.synchronize_terminal_approval(
            requisition=requisition,
            approval_request=approval,
            rejection_reason=decision.comments,
        )

        await self.approvals.flush()
        await self.requisitions.flush()

        return requisition, approval

    async def _load_for_decision(
        self,
        *,
        tenant_id: UUID,
        requisition_id: UUID,
    ) -> tuple[
        PurchaseRequisition,
        ProcurementApprovalRequest,
    ]:
        requisition = await self.requisitions.get_by_id(
            tenant_id=tenant_id,
            requisition_id=requisition_id,
            for_update=True,
        )

        if requisition is None:
            raise RequisitionNotFoundError(
                "purchase requisition not found"
            )

        approval = await self.approvals.get_by_object(
            tenant_id=tenant_id,
            object_type=ApprovalObjectType.PURCHASE_REQUISITION,
            object_id=requisition_id,
            for_update=True,
        )

        if approval is None:
            raise RequisitionApprovalNotFoundError(
                "purchase requisition approval request not found"
            )

        return requisition, approval
