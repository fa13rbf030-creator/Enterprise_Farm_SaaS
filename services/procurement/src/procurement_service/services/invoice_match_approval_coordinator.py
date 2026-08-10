from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    SupplierInvoiceMatch,
)
from procurement_service.repositories.approval import (
    ProcurementApprovalRepository,
)
from procurement_service.repositories.invoice_match import (
    SupplierInvoiceMatchRepository,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.approval import (
    ApprovalWorkflowService,
)
from procurement_service.services.invoice_match_approval import (
    InvoiceMatchApprovalIntegrationService,
)


class InvoiceMatchApprovalCoordinatorError(ValueError):
    """Base invoice-match approval coordinator error."""


class InvoiceMatchNotFoundError(
    InvoiceMatchApprovalCoordinatorError
):
    """Raised when invoice match is not found."""


class DuplicateInvoiceMatchApprovalError(
    InvoiceMatchApprovalCoordinatorError
):
    """Raised when invoice match already has approval."""


class InvoiceMatchApprovalNotFoundError(
    InvoiceMatchApprovalCoordinatorError
):
    """Raised when approval request is not found."""


class InvoiceMatchApprovalCoordinator:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.invoice_matches = SupplierInvoiceMatchRepository(
            session
        )
        self.approvals = ProcurementApprovalRepository(
            session
        )

    async def submit_for_approval(
        self,
        *,
        tenant_id: UUID,
        invoice_match_id: UUID,
        payload: ProcurementApprovalRequestCreate,
    ) -> tuple[
        SupplierInvoiceMatch,
        ProcurementApprovalRequest,
    ]:
        if payload.object_type != ApprovalObjectType.INVOICE_MATCH:
            raise InvoiceMatchApprovalCoordinatorError(
                "approval payload must target an invoice match"
            )

        if payload.object_id != invoice_match_id:
            raise InvoiceMatchApprovalCoordinatorError(
                "approval payload object does not match invoice match"
            )

        invoice_match = await self.invoice_matches.get_by_id(
            tenant_id=tenant_id,
            invoice_match_id=invoice_match_id,
            for_update=True,
        )

        if invoice_match is None:
            raise InvoiceMatchNotFoundError(
                "invoice match not found"
            )

        existing = await self.approvals.get_by_object(
            tenant_id=tenant_id,
            object_type=ApprovalObjectType.INVOICE_MATCH,
            object_id=invoice_match_id,
            for_update=True,
        )

        if existing is not None:
            raise DuplicateInvoiceMatchApprovalError(
                "invoice match already has an approval request"
            )

        InvoiceMatchApprovalIntegrationService.submit(
            invoice_match
        )

        approval = ApprovalWorkflowService.create_request(
            tenant_id=tenant_id,
            payload=payload,
        )

        await self.approvals.add(approval)

        return invoice_match, approval

    async def approve_step(
        self,
        *,
        tenant_id: UUID,
        invoice_match_id: UUID,
        step_number: int,
        decision: ProcurementApprovalStepDecision,
    ) -> tuple[
        SupplierInvoiceMatch,
        ProcurementApprovalRequest,
    ]:
        invoice_match, approval = await self._load_for_decision(
            tenant_id=tenant_id,
            invoice_match_id=invoice_match_id,
        )

        ApprovalWorkflowService.approve_step(
            request=approval,
            step_number=step_number,
            decision=decision,
        )

        if approval.status == ApprovalRequestStatus.APPROVED:
            InvoiceMatchApprovalIntegrationService.synchronize_outcome(
                invoice_match=invoice_match,
                approval=approval,
                decided_by=decision.decided_by,
            )

        await self.approvals.flush()
        await self.invoice_matches.flush()

        return invoice_match, approval

    async def reject_step(
        self,
        *,
        tenant_id: UUID,
        invoice_match_id: UUID,
        step_number: int,
        decision: ProcurementApprovalStepDecision,
    ) -> tuple[
        SupplierInvoiceMatch,
        ProcurementApprovalRequest,
    ]:
        invoice_match, approval = await self._load_for_decision(
            tenant_id=tenant_id,
            invoice_match_id=invoice_match_id,
        )

        ApprovalWorkflowService.reject_step(
            request=approval,
            step_number=step_number,
            decision=decision,
        )

        InvoiceMatchApprovalIntegrationService.synchronize_outcome(
            invoice_match=invoice_match,
            approval=approval,
            decided_by=decision.decided_by,
            rejection_reason=decision.comments,
        )

        await self.approvals.flush()
        await self.invoice_matches.flush()

        return invoice_match, approval

    async def _load_for_decision(
        self,
        *,
        tenant_id: UUID,
        invoice_match_id: UUID,
    ) -> tuple[
        SupplierInvoiceMatch,
        ProcurementApprovalRequest,
    ]:
        invoice_match = await self.invoice_matches.get_by_id(
            tenant_id=tenant_id,
            invoice_match_id=invoice_match_id,
            for_update=True,
        )

        if invoice_match is None:
            raise InvoiceMatchNotFoundError(
                "invoice match not found"
            )

        approval = await self.approvals.get_by_object(
            tenant_id=tenant_id,
            object_type=ApprovalObjectType.INVOICE_MATCH,
            object_id=invoice_match_id,
            for_update=True,
        )

        if approval is None:
            raise InvoiceMatchApprovalNotFoundError(
                "invoice match approval request not found"
            )

        return invoice_match, approval
