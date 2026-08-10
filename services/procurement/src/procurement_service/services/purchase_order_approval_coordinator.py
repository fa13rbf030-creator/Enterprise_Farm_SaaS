from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    PurchaseOrder,
)
from procurement_service.repositories.approval import (
    ProcurementApprovalRepository,
)
from procurement_service.repositories.purchase_order import (
    PurchaseOrderRepository,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.approval import (
    ApprovalWorkflowService,
)
from procurement_service.services.purchase_order_approval import (
    PurchaseOrderApprovalIntegrationService,
)


class PurchaseOrderApprovalCoordinatorError(ValueError):
    """Base purchase-order approval coordinator error."""


class PurchaseOrderNotFoundError(
    PurchaseOrderApprovalCoordinatorError
):
    """Raised when the purchase order does not exist."""


class DuplicatePurchaseOrderApprovalError(
    PurchaseOrderApprovalCoordinatorError
):
    """Raised when the PO already has an approval request."""


class PurchaseOrderApprovalNotFoundError(
    PurchaseOrderApprovalCoordinatorError
):
    """Raised when the PO approval request does not exist."""


class PurchaseOrderApprovalCoordinator:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.purchase_orders = PurchaseOrderRepository(session)
        self.approvals = ProcurementApprovalRepository(session)

    async def submit_for_approval(
        self,
        *,
        tenant_id: UUID,
        purchase_order_id: UUID,
        payload: ProcurementApprovalRequestCreate,
    ) -> tuple[PurchaseOrder, ProcurementApprovalRequest]:
        if payload.object_type != ApprovalObjectType.PURCHASE_ORDER:
            raise PurchaseOrderApprovalCoordinatorError(
                "approval payload must target a purchase order"
            )

        if payload.object_id != purchase_order_id:
            raise PurchaseOrderApprovalCoordinatorError(
                "approval payload object does not match purchase order"
            )

        purchase_order = await self.purchase_orders.get_by_id(
            tenant_id=tenant_id,
            purchase_order_id=purchase_order_id,
            for_update=True,
        )

        if purchase_order is None:
            raise PurchaseOrderNotFoundError(
                "purchase order not found"
            )

        existing = await self.approvals.get_by_object(
            tenant_id=tenant_id,
            object_type=ApprovalObjectType.PURCHASE_ORDER,
            object_id=purchase_order_id,
            for_update=True,
        )

        if existing is not None:
            raise DuplicatePurchaseOrderApprovalError(
                "purchase order already has an approval request"
            )

        PurchaseOrderApprovalIntegrationService.submit(
            purchase_order
        )

        approval = ApprovalWorkflowService.create_request(
            tenant_id=tenant_id,
            payload=payload,
        )

        await self.approvals.add(approval)

        return purchase_order, approval

    async def approve_step(
        self,
        *,
        tenant_id: UUID,
        purchase_order_id: UUID,
        step_number: int,
        decision: ProcurementApprovalStepDecision,
    ) -> tuple[PurchaseOrder, ProcurementApprovalRequest]:
        purchase_order, approval = await self._load_for_decision(
            tenant_id=tenant_id,
            purchase_order_id=purchase_order_id,
        )

        ApprovalWorkflowService.approve_step(
            request=approval,
            step_number=step_number,
            decision=decision,
        )

        if approval.status == ApprovalRequestStatus.APPROVED:
            PurchaseOrderApprovalIntegrationService.synchronize_outcome(
                purchase_order,
                approval,
                decided_by=decision.decided_by,
            )

        await self.approvals.flush()

        return purchase_order, approval

    async def reject_step(
        self,
        *,
        tenant_id: UUID,
        purchase_order_id: UUID,
        step_number: int,
        decision: ProcurementApprovalStepDecision,
    ) -> tuple[PurchaseOrder, ProcurementApprovalRequest]:
        purchase_order, approval = await self._load_for_decision(
            tenant_id=tenant_id,
            purchase_order_id=purchase_order_id,
        )

        ApprovalWorkflowService.reject_step(
            request=approval,
            step_number=step_number,
            decision=decision,
        )

        PurchaseOrderApprovalIntegrationService.synchronize_outcome(
            purchase_order,
            approval,
            decided_by=decision.decided_by,
            rejection_reason=decision.comments,
        )

        await self.approvals.flush()

        return purchase_order, approval

    async def _load_for_decision(
        self,
        *,
        tenant_id: UUID,
        purchase_order_id: UUID,
    ) -> tuple[PurchaseOrder, ProcurementApprovalRequest]:
        purchase_order = await self.purchase_orders.get_by_id(
            tenant_id=tenant_id,
            purchase_order_id=purchase_order_id,
            for_update=True,
        )

        if purchase_order is None:
            raise PurchaseOrderNotFoundError(
                "purchase order not found"
            )

        approval = await self.approvals.get_by_object(
            tenant_id=tenant_id,
            object_type=ApprovalObjectType.PURCHASE_ORDER,
            object_id=purchase_order_id,
            for_update=True,
        )

        if approval is None:
            raise PurchaseOrderApprovalNotFoundError(
                "purchase order approval request not found"
            )

        return purchase_order, approval
