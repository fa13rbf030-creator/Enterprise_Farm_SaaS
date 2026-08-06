from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    AccountStatus,
    FiscalPeriodStatus,
    JournalSource,
    OpeningBalanceStatus,
)
from finance_service.models.closing import (
    OpeningBalanceBatch,
    OpeningBalanceLine,
)
from finance_service.repositories.closing import (
    get_opening_balance_batch,
    list_opening_balance_lines,
)
from finance_service.repositories.gl import (
    get_account,
    get_fiscal_period,
)
from finance_service.schemas.closing import (
    OpeningBalanceBatchCreate,
)
from finance_service.schemas.gl import (
    JournalEntryCreate,
    JournalLineCreate,
)
from finance_service.services.gl import (
    create_draft_journal,
)
from finance_service.services.opening_balances import (
    OpeningBalanceValidationError,
    validate_opening_balance_batch,
)
from finance_service.services.posting import post_journal


class OpeningBalanceWorkflowError(ValueError):
    pass


async def create_opening_balance_batch(
    session: AsyncSession,
    *,
    payload: OpeningBalanceBatchCreate,
) -> OpeningBalanceBatch:
    period = await get_fiscal_period(
        session,
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
    )

    if period is None:
        raise OpeningBalanceWorkflowError(
            "Fiscal period not found"
        )

    if period.status != FiscalPeriodStatus.OPEN:
        raise OpeningBalanceWorkflowError(
            "Opening balances require an open period"
        )

    try:
        total_debit, total_credit = (
            validate_opening_balance_batch(payload)
        )
    except OpeningBalanceValidationError as exc:
        raise OpeningBalanceWorkflowError(
            str(exc)
        ) from exc

    for line in payload.lines:
        account = await get_account(
            session,
            tenant_id=payload.tenant_id,
            account_id=line.ledger_account_id,
        )

        if account is None:
            raise OpeningBalanceWorkflowError(
                "Opening-balance account not found"
            )

        if account.status != AccountStatus.ACTIVE:
            raise OpeningBalanceWorkflowError(
                "Opening-balance account is not active"
            )

    batch = OpeningBalanceBatch(
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
        batch_number=payload.batch_number.strip(),
        description=payload.description.strip(),
        status=OpeningBalanceStatus.DRAFT,
        total_debit=total_debit,
        total_credit=total_credit,
        created_by=payload.created_by,
    )

    session.add(batch)
    await session.flush()

    for line in payload.lines:
        session.add(
            OpeningBalanceLine(
                tenant_id=payload.tenant_id,
                batch_id=batch.id,
                ledger_account_id=line.ledger_account_id,
                debit=line.debit,
                credit=line.credit,
                description=line.description.strip(),
            )
        )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise OpeningBalanceWorkflowError(
            "Opening-balance batch number already exists"
        ) from exc

    await session.refresh(batch)
    return batch


async def validate_opening_balance_batch_record(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
    validated_by: UUID,
) -> OpeningBalanceBatch:
    batch = await get_opening_balance_batch(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
        for_update=True,
    )

    if batch is None:
        raise OpeningBalanceWorkflowError(
            "Opening-balance batch not found"
        )

    if batch.status != OpeningBalanceStatus.DRAFT:
        raise OpeningBalanceWorkflowError(
            "Only draft opening-balance batches "
            "can be validated"
        )

    lines = await list_opening_balance_lines(
        session,
        tenant_id=tenant_id,
        batch_id=batch.id,
    )

    if len(lines) < 2:
        raise OpeningBalanceWorkflowError(
            "Opening-balance batch requires two lines"
        )

    batch.status = OpeningBalanceStatus.VALIDATED
    batch.validated_by = validated_by

    await session.commit()
    await session.refresh(batch)

    return batch


async def post_opening_balance_batch(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
    posted_by: UUID,
    journal_number: str,
) -> OpeningBalanceBatch:
    batch = await get_opening_balance_batch(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
        for_update=True,
    )

    if batch is None:
        raise OpeningBalanceWorkflowError(
            "Opening-balance batch not found"
        )

    if batch.status != OpeningBalanceStatus.VALIDATED:
        raise OpeningBalanceWorkflowError(
            "Opening-balance batch must be validated"
        )

    period = await get_fiscal_period(
        session,
        tenant_id=tenant_id,
        fiscal_period_id=batch.fiscal_period_id,
    )

    if period is None:
        raise OpeningBalanceWorkflowError(
            "Fiscal period not found"
        )

    if period.status != FiscalPeriodStatus.OPEN:
        raise OpeningBalanceWorkflowError(
            "Opening balances cannot post to a closed period"
        )

    lines = await list_opening_balance_lines(
        session,
        tenant_id=tenant_id,
        batch_id=batch.id,
    )

    journal_payload = JournalEntryCreate(
        tenant_id=tenant_id,
        fiscal_period_id=batch.fiscal_period_id,
        journal_number=journal_number,
        entry_date=period.starts_on,
        source=JournalSource.SYSTEM,
        source_reference=str(batch.id),
        description=(
            batch.description
            or f"Opening balance batch {batch.batch_number}"
        ),
        created_by=posted_by,
        lines=[
            JournalLineCreate(
                ledger_account_id=line.ledger_account_id,
                line_number=index,
                description=line.description,
                debit=line.debit,
                credit=line.credit,
            )
            for index, line in enumerate(lines, start=1)
        ],
    )

    journal = await create_draft_journal(
        session,
        payload=journal_payload,
    )

    await post_journal(
        session,
        tenant_id=tenant_id,
        journal_id=journal.id,
        posted_by=posted_by,
    )

    batch = await get_opening_balance_batch(
        session,
        tenant_id=tenant_id,
        batch_id=batch_id,
        for_update=True,
    )

    if batch is None:
        raise OpeningBalanceWorkflowError(
            "Opening-balance batch disappeared"
        )

    batch.status = OpeningBalanceStatus.POSTED
    batch.posted_journal_id = journal.id

    await session.commit()
    await session.refresh(batch)

    return batch
