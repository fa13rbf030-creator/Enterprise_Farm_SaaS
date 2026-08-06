from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    BankAccountStatus,
    FraudCheckStatus,
    SettlementStatus,
    TreasuryApprovalDecision,
    TreasuryFileFormat,
    TreasuryPaymentBatchStatus,
    TreasuryPaymentItemStatus,
)
from finance_service.models.treasury import (
    LiquidityForecast,
    TreasuryBatchApproval,
    TreasuryPaymentBatch,
    TreasuryPaymentItem,
)
from finance_service.repositories.banking import (
    get_bank_account,
)
from finance_service.repositories.treasury import (
    get_batch_approval,
    get_treasury_batch,
    get_treasury_item,
    list_batch_approvals,
    list_treasury_batches,
    list_treasury_items,
)
from finance_service.schemas.treasury import (
    LiquidityForecastCreate,
    SettlementConfirmationCreate,
    TreasuryBatchApprovalCreate,
    TreasuryDashboardRead,
    TreasuryFraudReviewRead,
    TreasuryPaymentBatchCreate,
    TreasuryPaymentBatchFullRead,
    TreasuryPaymentFileRead,
)
from finance_service.services.iso20022 import (
    Iso20022GenerationError,
    generate_pain001_xml,
)
from finance_service.services.treasury_calculations import (
    calculate_liquidity_projection,
    calculate_payment_batch_total,
    evaluate_basic_payment_fraud,
    quantize_treasury_money,
)


class TreasuryWorkflowError(ValueError):
    pass


DEFAULT_PAYMENT_DAILY_LIMIT = Decimal("1000000")


async def create_payment_batch(
    session: AsyncSession,
    *,
    payload: TreasuryPaymentBatchCreate,
) -> TreasuryPaymentBatch:
    bank_account = await get_bank_account(
        session,
        tenant_id=payload.tenant_id,
        bank_account_id=payload.bank_account_id,
    )

    if bank_account is None:
        raise TreasuryWorkflowError(
            "Treasury bank account not found"
        )

    if bank_account.status != BankAccountStatus.ACTIVE:
        raise TreasuryWorkflowError(
            "Treasury bank account is not active"
        )

    if (
        bank_account.currency_code.upper()
        != payload.currency_code.upper()
    ):
        raise TreasuryWorkflowError(
            "Batch currency does not match bank account"
        )

    total_amount, item_count = (
        calculate_payment_batch_total(payload)
    )

    batch = TreasuryPaymentBatch(
        tenant_id=payload.tenant_id,
        batch_number=payload.batch_number.strip(),
        batch_date=payload.batch_date,
        execution_date=payload.execution_date,
        bank_account_id=payload.bank_account_id,
        currency_code=payload.currency_code.upper(),
        total_amount=total_amount,
        item_count=item_count,
        file_format=payload.file_format,
        created_by=payload.created_by,
        notes=payload.notes.strip(),
    )

    session.add(batch)
    await session.flush()

    for item_payload in payload.items:
        duplicate_reference = await session.scalar(
            select(
                func.count(TreasuryPaymentItem.id)
            ).where(
                TreasuryPaymentItem.tenant_id
                == payload.tenant_id,
                TreasuryPaymentItem.payment_reference
                == item_payload.payment_reference,
            )
        )

        fraud_status, fraud_reason = (
            evaluate_basic_payment_fraud(
                amount=item_payload.amount,
                duplicate_reference=bool(
                    duplicate_reference
                ),
                beneficiary_changed=False,
                daily_limit=DEFAULT_PAYMENT_DAILY_LIMIT,
            )
        )

        item = TreasuryPaymentItem(
            tenant_id=payload.tenant_id,
            batch_id=batch.id,
            line_number=item_payload.line_number,
            vendor_id=item_payload.vendor_id,
            vendor_payment_id=(
                item_payload.vendor_payment_id
            ),
            payment_reference=(
                item_payload.payment_reference.strip()
            ),
            beneficiary_name=(
                item_payload.beneficiary_name.strip()
            ),
            beneficiary_account=(
                item_payload.beneficiary_account.strip()
            ),
            beneficiary_iban=(
                item_payload.beneficiary_iban.strip()
                if item_payload.beneficiary_iban
                else None
            ),
            beneficiary_bank_code=(
                item_payload.beneficiary_bank_code
            ),
            amount=item_payload.amount,
            currency_code=(
                item_payload.currency_code.upper()
            ),
            fraud_check_status=fraud_status,
            fraud_reason=fraud_reason,
        )

        session.add(item)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TreasuryWorkflowError(
            "Batch number or payment reference "
            "already exists"
        ) from exc

    await session.refresh(batch)
    return batch


async def get_payment_batch_detail(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
) -> TreasuryPaymentBatchFullRead:
    batch = await get_treasury_batch(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
    )

    if batch is None:
        raise TreasuryWorkflowError(
            "Treasury payment batch not found"
        )

    items = await list_treasury_items(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
    )

    approvals = await list_batch_approvals(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
    )

    return TreasuryPaymentBatchFullRead(
        **batch.__dict__,
        items=items,
        approvals=approvals,
    )


async def review_batch_fraud(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
) -> TreasuryFraudReviewRead:
    batch = await get_treasury_batch(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
    )

    if batch is None:
        raise TreasuryWorkflowError(
            "Treasury payment batch not found"
        )

    items = await list_treasury_items(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
    )

    passed = sum(
        1
        for item in items
        if item.fraud_check_status
        == FraudCheckStatus.PASSED
    )

    review_required = sum(
        1
        for item in items
        if item.fraud_check_status
        == FraudCheckStatus.REVIEW_REQUIRED
    )

    blocked = sum(
        1
        for item in items
        if item.fraud_check_status
        == FraudCheckStatus.BLOCKED
    )

    return TreasuryFraudReviewRead(
        batch_id=batch.id,
        passed=passed,
        review_required=review_required,
        blocked=blocked,
        can_submit_for_approval=blocked == 0,
    )


async def submit_batch_for_approval(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
    submitted_by: UUID,
) -> TreasuryPaymentBatch:
    batch = await get_treasury_batch(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
        for_update=True,
    )

    if batch is None:
        raise TreasuryWorkflowError(
            "Treasury payment batch not found"
        )

    if batch.status != TreasuryPaymentBatchStatus.DRAFT:
        raise TreasuryWorkflowError(
            "Only draft batches can be submitted"
        )

    if batch.created_by != submitted_by:
        raise TreasuryWorkflowError(
            "Only batch maker can submit for approval"
        )

    fraud_review = await review_batch_fraud(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
    )

    if fraud_review.blocked > 0:
        raise TreasuryWorkflowError(
            "Blocked payment items prevent submission"
        )

    batch.status = (
        TreasuryPaymentBatchStatus.PENDING_APPROVAL
    )

    await session.commit()
    await session.refresh(batch)

    return batch


async def decide_batch_approval(
    session: AsyncSession,
    *,
    batch_id: UUID,
    payload: TreasuryBatchApprovalCreate,
) -> TreasuryPaymentBatch:
    batch = await get_treasury_batch(
        session,
        tenant_id=payload.tenant_id,
        batch_id=batch_id,
        for_update=True,
    )

    if batch is None:
        raise TreasuryWorkflowError(
            "Treasury payment batch not found"
        )

    if (
        batch.status
        != TreasuryPaymentBatchStatus.PENDING_APPROVAL
    ):
        raise TreasuryWorkflowError(
            "Batch is not pending approval"
        )

    if batch.created_by == payload.approver_id:
        raise TreasuryWorkflowError(
            "Maker cannot approve own payment batch"
        )

    existing = await get_batch_approval(
        session,
        tenant_id=payload.tenant_id,
        batch_id=batch.id,
        approver_id=payload.approver_id,
    )

    if existing is not None:
        raise TreasuryWorkflowError(
            "Approver already decided this batch"
        )

    approval = TreasuryBatchApproval(
        tenant_id=payload.tenant_id,
        batch_id=batch.id,
        approver_id=payload.approver_id,
        decision=payload.decision,
        comments=payload.comments.strip(),
    )

    session.add(approval)

    items = await list_treasury_items(
        session,
        tenant_id=payload.tenant_id,
        batch_id=batch.id,
    )

    if (
        payload.decision
        == TreasuryApprovalDecision.APPROVED
    ):
        batch.status = TreasuryPaymentBatchStatus.APPROVED
        batch.approved_by = payload.approver_id

        for item in items:
            item.status = TreasuryPaymentItemStatus.APPROVED
    else:
        batch.status = TreasuryPaymentBatchStatus.REJECTED

        for item in items:
            item.status = TreasuryPaymentItemStatus.REJECTED

    await session.commit()
    await session.refresh(batch)

    return batch


async def generate_payment_file(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
) -> TreasuryPaymentFileRead:
    batch = await get_treasury_batch(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
        for_update=True,
    )

    if batch is None:
        raise TreasuryWorkflowError(
            "Treasury payment batch not found"
        )

    if batch.status not in {
        TreasuryPaymentBatchStatus.APPROVED,
        TreasuryPaymentBatchStatus.GENERATED,
    }:
        raise TreasuryWorkflowError(
            "Only approved batches can generate files"
        )

    if (
        batch.file_format
        != TreasuryFileFormat.ISO20022_PAIN_001
    ):
        raise TreasuryWorkflowError(
            "Only ISO 20022 pain.001 generation "
            "is implemented"
        )

    bank_account = await get_bank_account(
        session,
        tenant_id=tenant_id,
        bank_account_id=batch.bank_account_id,
    )

    if bank_account is None:
        raise TreasuryWorkflowError(
            "Treasury bank account not found"
        )

    items = await list_treasury_items(
        session,
        tenant_id=tenant_id,
        batch_id=batch.id,
    )

    try:
        content, digest = generate_pain001_xml(
            batch=batch,
            bank_account=bank_account,
            items=items,
        )
    except Iso20022GenerationError as exc:
        raise TreasuryWorkflowError(str(exc)) from exc

    file_name = f"{batch.batch_number}.xml"

    batch.payment_file_name = file_name
    batch.payment_file_hash = digest
    batch.status = TreasuryPaymentBatchStatus.GENERATED

    await session.commit()
    await session.refresh(batch)

    return TreasuryPaymentFileRead(
        batch_id=batch.id,
        file_name=file_name,
        file_format=batch.file_format,
        sha256=digest,
        content=content,
    )


async def submit_batch_to_bank(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
    submitted_by: UUID,
    external_submission_id: str,
) -> TreasuryPaymentBatch:
    batch = await get_treasury_batch(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
        for_update=True,
    )

    if batch is None:
        raise TreasuryWorkflowError(
            "Treasury payment batch not found"
        )

    if batch.status != TreasuryPaymentBatchStatus.GENERATED:
        raise TreasuryWorkflowError(
            "Payment file must be generated first"
        )

    if batch.created_by == submitted_by:
        raise TreasuryWorkflowError(
            "Maker cannot submit own batch to bank"
        )

    items = await list_treasury_items(
        session,
        tenant_id=tenant_id,
        batch_id=batch.id,
    )

    batch.status = TreasuryPaymentBatchStatus.SUBMITTED
    batch.external_submission_id = (
        external_submission_id.strip()
    )
    batch.submitted_at = datetime.now(UTC)

    for item in items:
        item.status = TreasuryPaymentItemStatus.SUBMITTED

    await session.commit()
    await session.refresh(batch)

    return batch


async def confirm_item_settlement(
    session: AsyncSession,
    *,
    item_id: UUID,
    payload: SettlementConfirmationCreate,
) -> TreasuryPaymentBatch:
    item = await get_treasury_item(
        session,
        tenant_id=payload.tenant_id,
        item_id=item_id,
        for_update=True,
    )

    if item is None:
        raise TreasuryWorkflowError(
            "Treasury payment item not found"
        )

    batch = await get_treasury_batch(
        session,
        tenant_id=payload.tenant_id,
        batch_id=item.batch_id,
        for_update=True,
    )

    if batch is None:
        raise TreasuryWorkflowError(
            "Treasury payment batch not found"
        )

    if batch.status not in {
        TreasuryPaymentBatchStatus.SUBMITTED,
        TreasuryPaymentBatchStatus.PARTIALLY_SETTLED,
    }:
        raise TreasuryWorkflowError(
            "Batch has not been submitted to bank"
        )

    item.settlement_reference = (
        payload.settlement_reference.strip()
    )
    item.settlement_status = payload.settlement_status
    item.failure_reason = payload.failure_reason

    if (
        payload.settlement_status
        == SettlementStatus.CONFIRMED
    ):
        item.status = TreasuryPaymentItemStatus.SETTLED
    else:
        item.status = TreasuryPaymentItemStatus.FAILED

    items = await list_treasury_items(
        session,
        tenant_id=payload.tenant_id,
        batch_id=batch.id,
    )

    effective_statuses = [
        (
            item.status
            if existing.id == item.id
            else existing.status
        )
        for existing in items
    ]

    settled_count = sum(
        1
        for status in effective_statuses
        if status == TreasuryPaymentItemStatus.SETTLED
    )

    failed_count = sum(
        1
        for status in effective_statuses
        if status == TreasuryPaymentItemStatus.FAILED
    )

    if settled_count == len(effective_statuses):
        batch.status = TreasuryPaymentBatchStatus.SETTLED
        batch.settled_at = datetime.now(UTC)
    elif settled_count > 0:
        batch.status = (
            TreasuryPaymentBatchStatus.PARTIALLY_SETTLED
        )
    elif failed_count == len(effective_statuses):
        batch.status = TreasuryPaymentBatchStatus.FAILED

    await session.commit()
    await session.refresh(batch)

    return batch


async def create_liquidity_forecast(
    session: AsyncSession,
    *,
    payload: LiquidityForecastCreate,
) -> LiquidityForecast:
    projected_closing, funding_gap = (
        calculate_liquidity_projection(
            opening_cash=payload.opening_cash,
            expected_inflows=payload.expected_inflows,
            expected_outflows=payload.expected_outflows,
            minimum_cash_buffer=(
                payload.minimum_cash_buffer
            ),
        )
    )

    forecast = LiquidityForecast(
        tenant_id=payload.tenant_id,
        forecast_date=payload.forecast_date,
        horizon_days=payload.horizon_days,
        currency_code=payload.currency_code.upper(),
        scenario=payload.scenario,
        opening_cash=payload.opening_cash,
        expected_inflows=payload.expected_inflows,
        expected_outflows=payload.expected_outflows,
        projected_closing_cash=projected_closing,
        minimum_cash_buffer=(
            payload.minimum_cash_buffer
        ),
        funding_gap=funding_gap,
        created_by=payload.created_by,
    )

    session.add(forecast)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TreasuryWorkflowError(
            "Liquidity forecast already exists "
            "for this date, currency and scenario"
        ) from exc

    await session.refresh(forecast)
    return forecast


async def build_treasury_dashboard(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> TreasuryDashboardRead:
    batches = await list_treasury_batches(
        session,
        tenant_id=tenant_id,
    )

    def count_status(status):
        return sum(
            1
            for batch in batches
            if batch.status == status
        )

    pending_statuses = {
        TreasuryPaymentBatchStatus.DRAFT,
        TreasuryPaymentBatchStatus.PENDING_APPROVAL,
        TreasuryPaymentBatchStatus.APPROVED,
        TreasuryPaymentBatchStatus.GENERATED,
    }

    submitted_statuses = {
        TreasuryPaymentBatchStatus.SUBMITTED,
        TreasuryPaymentBatchStatus.PARTIALLY_SETTLED,
    }

    pending_amount = sum(
        (
            batch.total_amount
            for batch in batches
            if batch.status in pending_statuses
        ),
        Decimal("0"),
    )

    submitted_amount = sum(
        (
            batch.total_amount
            for batch in batches
            if batch.status in submitted_statuses
        ),
        Decimal("0"),
    )

    return TreasuryDashboardRead(
        tenant_id=tenant_id,
        draft_batches=count_status(
            TreasuryPaymentBatchStatus.DRAFT
        ),
        pending_approval_batches=count_status(
            TreasuryPaymentBatchStatus.PENDING_APPROVAL
        ),
        approved_batches=count_status(
            TreasuryPaymentBatchStatus.APPROVED
        ),
        submitted_batches=count_status(
            TreasuryPaymentBatchStatus.SUBMITTED
        )
        + count_status(
            TreasuryPaymentBatchStatus.PARTIALLY_SETTLED
        ),
        settled_batches=count_status(
            TreasuryPaymentBatchStatus.SETTLED
        ),
        failed_batches=count_status(
            TreasuryPaymentBatchStatus.FAILED
        ),
        total_pending_amount=quantize_treasury_money(
            pending_amount
        ),
        total_submitted_amount=quantize_treasury_money(
            submitted_amount
        ),
    )
