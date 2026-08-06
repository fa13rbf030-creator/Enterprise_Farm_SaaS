from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    AccountStatus,
    AccountType,
    CreditNoteStatus,
    CustomerStatus,
    FiscalPeriodStatus,
    InvoiceStatus,
    JournalSource,
    ReceiptStatus,
)
from finance_service.models.ar import (
    CustomerAccount,
    CustomerCreditNote,
    CustomerInvoice,
    CustomerInvoiceLine,
    CustomerReceipt,
    ReceiptAllocation,
)
from finance_service.repositories.ar import (
    get_credit_note,
    get_customer,
    get_invoice,
    get_receipt,
    get_receipt_allocation,
    list_invoice_lines,
    list_outstanding_invoices,
)
from finance_service.repositories.gl import (
    get_account,
    get_fiscal_period,
)
from finance_service.schemas.ar import (
    CreditNoteCreate,
    CustomerAgingRead,
    CustomerCreate,
    InvoiceCreate,
    InvoiceDetailRead,
    InvoiceLineRead,
    ReceiptAllocationCreate,
    ReceiptCreate,
)
from finance_service.schemas.gl import (
    JournalEntryCreate,
    JournalLineCreate,
)
from finance_service.services.ar_calculations import (
    ArCalculationError,
    calculate_aging_bucket,
    calculate_invoice_totals,
    calculate_outstanding_amount,
    quantize_money,
)
from finance_service.services.gl import create_draft_journal
from finance_service.services.posting import post_journal


class ArWorkflowError(ValueError):
    pass


async def _require_open_period(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_period_id: UUID,
    transaction_date: date,
):
    period = await get_fiscal_period(
        session,
        tenant_id=tenant_id,
        fiscal_period_id=fiscal_period_id,
    )

    if period is None:
        raise ArWorkflowError(
            "Fiscal period not found"
        )

    if period.status != FiscalPeriodStatus.OPEN:
        raise ArWorkflowError(
            "AR transaction requires an open period"
        )

    if not (
        period.starts_on
        <= transaction_date
        <= period.ends_on
    ):
        raise ArWorkflowError(
            "AR transaction date is outside fiscal period"
        )

    return period


async def _require_account(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    account_id: UUID,
    expected_type: AccountType | None = None,
):
    account = await get_account(
        session,
        tenant_id=tenant_id,
        account_id=account_id,
    )

    if account is None:
        raise ArWorkflowError(
            "Ledger account not found in tenant"
        )

    if account.status != AccountStatus.ACTIVE:
        raise ArWorkflowError(
            "Ledger account is not active"
        )

    if (
        expected_type is not None
        and account.account_type != expected_type
    ):
        raise ArWorkflowError(
            f"Ledger account must be {expected_type.value}"
        )

    return account


async def create_customer(
    session: AsyncSession,
    *,
    payload: CustomerCreate,
) -> CustomerAccount:
    await _require_account(
        session,
        tenant_id=payload.tenant_id,
        account_id=payload.ar_control_account_id,
        expected_type=AccountType.ASSET,
    )

    await _require_account(
        session,
        tenant_id=payload.tenant_id,
        account_id=payload.revenue_account_id,
        expected_type=AccountType.REVENUE,
    )

    if payload.tax_account_id is not None:
        await _require_account(
            session,
            tenant_id=payload.tenant_id,
            account_id=payload.tax_account_id,
            expected_type=AccountType.LIABILITY,
        )

    customer = CustomerAccount(
        tenant_id=payload.tenant_id,
        customer_code=payload.customer_code.strip(),
        name=payload.name.strip(),
        email=(
            str(payload.email)
            if payload.email is not None
            else None
        ),
        phone=payload.phone,
        billing_address=payload.billing_address.strip(),
        currency_code=payload.currency_code.upper(),
        credit_limit=payload.credit_limit,
        payment_terms_days=payload.payment_terms_days,
        ar_control_account_id=(
            payload.ar_control_account_id
        ),
        revenue_account_id=payload.revenue_account_id,
        tax_account_id=payload.tax_account_id,
        is_tax_registered=payload.is_tax_registered,
        tax_registration_number=(
            payload.tax_registration_number
        ),
    )

    session.add(customer)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ArWorkflowError(
            "Customer code already exists in tenant"
        ) from exc

    await session.refresh(customer)
    return customer


async def create_invoice(
    session: AsyncSession,
    *,
    payload: InvoiceCreate,
) -> CustomerInvoice:
    customer = await get_customer(
        session,
        tenant_id=payload.tenant_id,
        customer_id=payload.customer_id,
    )

    if customer is None:
        raise ArWorkflowError("Customer not found")

    if customer.status != CustomerStatus.ACTIVE:
        raise ArWorkflowError(
            "Customer is not active"
        )

    await _require_open_period(
        session,
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
        transaction_date=payload.invoice_date,
    )

    try:
        (
            subtotal,
            discount_total,
            tax_total,
            total_amount,
        ) = calculate_invoice_totals(payload)
    except ArCalculationError as exc:
        raise ArWorkflowError(str(exc)) from exc

    line_numbers: set[int] = set()

    for line in payload.lines:
        if line.line_number in line_numbers:
            raise ArWorkflowError(
                "Invoice line numbers must be unique"
            )

        line_numbers.add(line.line_number)

        await _require_account(
            session,
            tenant_id=payload.tenant_id,
            account_id=line.revenue_account_id,
            expected_type=AccountType.REVENUE,
        )

    invoice = CustomerInvoice(
        tenant_id=payload.tenant_id,
        customer_id=payload.customer_id,
        fiscal_period_id=payload.fiscal_period_id,
        invoice_number=payload.invoice_number.strip(),
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        currency_code=payload.currency_code.upper(),
        exchange_rate=payload.exchange_rate,
        subtotal=subtotal,
        discount_total=discount_total,
        tax_total=tax_total,
        total_amount=total_amount,
        outstanding_amount=total_amount,
        description=payload.description.strip(),
        created_by=payload.created_by,
    )

    session.add(invoice)
    await session.flush()

    for line in payload.lines:
        gross = quantize_money(
            line.quantity * line.unit_price
        )
        taxable = gross - line.discount_amount
        tax_amount = quantize_money(
            taxable
            * line.tax_rate
            / Decimal("100")
        )
        line_total = quantize_money(
            taxable + tax_amount
        )

        session.add(
            CustomerInvoiceLine(
                tenant_id=payload.tenant_id,
                invoice_id=invoice.id,
                line_number=line.line_number,
                description=line.description.strip(),
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_amount=line.discount_amount,
                tax_rate=line.tax_rate,
                tax_amount=tax_amount,
                line_total=line_total,
                revenue_account_id=(
                    line.revenue_account_id
                ),
            )
        )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ArWorkflowError(
            "Invoice number already exists in tenant"
        ) from exc

    await session.refresh(invoice)
    return invoice


async def get_invoice_detail(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    invoice_id: UUID,
) -> InvoiceDetailRead:
    invoice = await get_invoice(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice_id,
    )

    if invoice is None:
        raise ArWorkflowError("Invoice not found")

    lines = await list_invoice_lines(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice.id,
    )

    return InvoiceDetailRead(
        **invoice.__dict__,
        lines=[
            InvoiceLineRead.model_validate(line)
            for line in lines
        ],
    )


async def issue_invoice(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    invoice_id: UUID,
    issued_by: UUID,
) -> CustomerInvoice:
    invoice = await get_invoice(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        for_update=True,
    )

    if invoice is None:
        raise ArWorkflowError("Invoice not found")

    if invoice.status != InvoiceStatus.DRAFT:
        raise ArWorkflowError(
            "Only draft invoices can be issued"
        )

    customer = await get_customer(
        session,
        tenant_id=tenant_id,
        customer_id=invoice.customer_id,
    )

    if customer is None:
        raise ArWorkflowError("Customer not found")

    lines = await list_invoice_lines(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice.id,
    )

    journal_lines = [
        JournalLineCreate(
            ledger_account_id=customer.ar_control_account_id,
            line_number=1,
            description=f"Invoice {invoice.invoice_number}",
            debit=invoice.total_amount,
        )
    ]

    line_number = 2

    for line in lines:
        revenue_amount = quantize_money(
            line.line_total - line.tax_amount
        )

        if revenue_amount > 0:
            journal_lines.append(
                JournalLineCreate(
                    ledger_account_id=(
                        line.revenue_account_id
                    ),
                    line_number=line_number,
                    description=line.description,
                    credit=revenue_amount,
                )
            )
            line_number += 1

    if invoice.tax_total > 0:
        if customer.tax_account_id is None:
            raise ArWorkflowError(
                "Customer tax account is not configured"
            )

        journal_lines.append(
            JournalLineCreate(
                ledger_account_id=customer.tax_account_id,
                line_number=line_number,
                description="Output tax",
                credit=invoice.tax_total,
            )
        )

    journal = await create_draft_journal(
        session,
        payload=JournalEntryCreate(
            tenant_id=tenant_id,
            fiscal_period_id=invoice.fiscal_period_id,
            journal_number=(
                f"AR-{invoice.invoice_number}"
            ),
            entry_date=invoice.invoice_date,
            source=JournalSource.ACCOUNTS_RECEIVABLE,
            source_reference=str(invoice.id),
            description=(
                f"Customer invoice "
                f"{invoice.invoice_number}"
            ),
            created_by=issued_by,
            lines=journal_lines,
        ),
    )

    await post_journal(
        session,
        tenant_id=tenant_id,
        journal_id=journal.id,
        posted_by=issued_by,
    )

    invoice = await get_invoice(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        for_update=True,
    )

    if invoice is None:
        raise ArWorkflowError(
            "Invoice disappeared after posting"
        )

    invoice.status = InvoiceStatus.ISSUED
    invoice.journal_entry_id = journal.id
    invoice.issued_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(invoice)

    return invoice


async def create_receipt(
    session: AsyncSession,
    *,
    payload: ReceiptCreate,
) -> CustomerReceipt:
    customer = await get_customer(
        session,
        tenant_id=payload.tenant_id,
        customer_id=payload.customer_id,
    )

    if customer is None:
        raise ArWorkflowError("Customer not found")

    await _require_open_period(
        session,
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
        transaction_date=payload.receipt_date,
    )

    receipt = CustomerReceipt(
        tenant_id=payload.tenant_id,
        customer_id=payload.customer_id,
        fiscal_period_id=payload.fiscal_period_id,
        receipt_number=payload.receipt_number.strip(),
        receipt_date=payload.receipt_date,
        amount=payload.amount,
        allocated_amount=Decimal("0"),
        unallocated_amount=payload.amount,
        currency_code=payload.currency_code.upper(),
        exchange_rate=payload.exchange_rate,
        payment_method=payload.payment_method,
        reference_number=payload.reference_number,
        bank_account_id=payload.bank_account_id,
        created_by=payload.created_by,
    )

    session.add(receipt)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ArWorkflowError(
            "Receipt number already exists in tenant"
        ) from exc

    await session.refresh(receipt)
    return receipt


async def post_receipt(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    receipt_id: UUID,
    cash_account_id: UUID,
    posted_by: UUID,
) -> CustomerReceipt:
    receipt = await get_receipt(
        session,
        tenant_id=tenant_id,
        receipt_id=receipt_id,
        for_update=True,
    )

    if receipt is None:
        raise ArWorkflowError("Receipt not found")

    if receipt.status != ReceiptStatus.DRAFT:
        raise ArWorkflowError(
            "Only draft receipts can be posted"
        )

    customer = await get_customer(
        session,
        tenant_id=tenant_id,
        customer_id=receipt.customer_id,
    )

    if customer is None:
        raise ArWorkflowError("Customer not found")

    await _require_account(
        session,
        tenant_id=tenant_id,
        account_id=cash_account_id,
        expected_type=AccountType.ASSET,
    )

    journal = await create_draft_journal(
        session,
        payload=JournalEntryCreate(
            tenant_id=tenant_id,
            fiscal_period_id=receipt.fiscal_period_id,
            journal_number=(
                f"RCPT-{receipt.receipt_number}"
            ),
            entry_date=receipt.receipt_date,
            source=JournalSource.ACCOUNTS_RECEIVABLE,
            source_reference=str(receipt.id),
            description=(
                f"Customer receipt "
                f"{receipt.receipt_number}"
            ),
            created_by=posted_by,
            lines=[
                JournalLineCreate(
                    ledger_account_id=cash_account_id,
                    line_number=1,
                    description="Receipt cash/bank",
                    debit=receipt.amount,
                ),
                JournalLineCreate(
                    ledger_account_id=(
                        customer.ar_control_account_id
                    ),
                    line_number=2,
                    description="Reduce customer receivable",
                    credit=receipt.amount,
                ),
            ],
        ),
    )

    await post_journal(
        session,
        tenant_id=tenant_id,
        journal_id=journal.id,
        posted_by=posted_by,
    )

    receipt = await get_receipt(
        session,
        tenant_id=tenant_id,
        receipt_id=receipt_id,
        for_update=True,
    )

    if receipt is None:
        raise ArWorkflowError(
            "Receipt disappeared after posting"
        )

    receipt.status = ReceiptStatus.POSTED
    receipt.journal_entry_id = journal.id

    await session.commit()
    await session.refresh(receipt)

    return receipt


async def allocate_receipt(
    session: AsyncSession,
    *,
    receipt_id: UUID,
    payload: ReceiptAllocationCreate,
) -> CustomerReceipt:
    receipt = await get_receipt(
        session,
        tenant_id=payload.tenant_id,
        receipt_id=receipt_id,
        for_update=True,
    )

    if receipt is None:
        raise ArWorkflowError("Receipt not found")

    if receipt.status not in {
        ReceiptStatus.POSTED,
        ReceiptStatus.PARTIALLY_ALLOCATED,
    }:
        raise ArWorkflowError(
            "Receipt must be posted before allocation"
        )

    invoice = await get_invoice(
        session,
        tenant_id=payload.tenant_id,
        invoice_id=payload.invoice_id,
        for_update=True,
    )

    if invoice is None:
        raise ArWorkflowError("Invoice not found")

    if invoice.customer_id != receipt.customer_id:
        raise ArWorkflowError(
            "Receipt and invoice customers differ"
        )

    if payload.allocated_amount > receipt.unallocated_amount:
        raise ArWorkflowError(
            "Allocation exceeds unallocated receipt amount"
        )

    if payload.allocated_amount > invoice.outstanding_amount:
        raise ArWorkflowError(
            "Allocation exceeds invoice outstanding amount"
        )

    existing = await get_receipt_allocation(
        session,
        tenant_id=payload.tenant_id,
        receipt_id=receipt.id,
        invoice_id=invoice.id,
    )

    if existing is not None:
        raise ArWorkflowError(
            "Receipt is already allocated to invoice"
        )

    session.add(
        ReceiptAllocation(
            tenant_id=payload.tenant_id,
            receipt_id=receipt.id,
            invoice_id=invoice.id,
            allocated_amount=payload.allocated_amount,
            allocated_by=payload.allocated_by,
        )
    )

    receipt.allocated_amount = quantize_money(
        receipt.allocated_amount
        + payload.allocated_amount
    )
    receipt.unallocated_amount = quantize_money(
        receipt.amount - receipt.allocated_amount
    )

    invoice.paid_amount = quantize_money(
        invoice.paid_amount
        + payload.allocated_amount
    )
    invoice.outstanding_amount = (
        calculate_outstanding_amount(
            total_amount=invoice.total_amount,
            paid_amount=invoice.paid_amount,
            credited_amount=invoice.credited_amount,
        )
    )

    if invoice.outstanding_amount == 0:
        invoice.status = InvoiceStatus.PAID
    else:
        invoice.status = InvoiceStatus.PARTIALLY_PAID

    if receipt.unallocated_amount == 0:
        receipt.status = ReceiptStatus.ALLOCATED
    else:
        receipt.status = (
            ReceiptStatus.PARTIALLY_ALLOCATED
        )

    await session.commit()
    await session.refresh(receipt)

    return receipt


async def create_credit_note(
    session: AsyncSession,
    *,
    payload: CreditNoteCreate,
) -> CustomerCreditNote:
    customer = await get_customer(
        session,
        tenant_id=payload.tenant_id,
        customer_id=payload.customer_id,
    )

    if customer is None:
        raise ArWorkflowError("Customer not found")

    await _require_open_period(
        session,
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
        transaction_date=payload.credit_note_date,
    )

    if payload.invoice_id is not None:
        invoice = await get_invoice(
            session,
            tenant_id=payload.tenant_id,
            invoice_id=payload.invoice_id,
        )

        if invoice is None:
            raise ArWorkflowError("Invoice not found")

        if invoice.customer_id != payload.customer_id:
            raise ArWorkflowError(
                "Credit-note customer does not match invoice"
            )

        if (
            payload.amount + payload.tax_amount
            > invoice.outstanding_amount
        ):
            raise ArWorkflowError(
                "Credit note exceeds invoice outstanding amount"
            )

    credit_note = CustomerCreditNote(
        tenant_id=payload.tenant_id,
        customer_id=payload.customer_id,
        invoice_id=payload.invoice_id,
        fiscal_period_id=payload.fiscal_period_id,
        credit_note_number=(
            payload.credit_note_number.strip()
        ),
        credit_note_date=payload.credit_note_date,
        amount=payload.amount,
        tax_amount=payload.tax_amount,
        total_amount=quantize_money(
            payload.amount + payload.tax_amount
        ),
        reason=payload.reason.strip(),
        created_by=payload.created_by,
    )

    session.add(credit_note)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ArWorkflowError(
            "Credit-note number already exists in tenant"
        ) from exc

    await session.refresh(credit_note)
    return credit_note


async def issue_credit_note(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    credit_note_id: UUID,
    issued_by: UUID,
) -> CustomerCreditNote:
    credit_note = await get_credit_note(
        session,
        tenant_id=tenant_id,
        credit_note_id=credit_note_id,
        for_update=True,
    )

    if credit_note is None:
        raise ArWorkflowError("Credit note not found")

    if credit_note.status != CreditNoteStatus.DRAFT:
        raise ArWorkflowError(
            "Only draft credit notes can be issued"
        )

    customer = await get_customer(
        session,
        tenant_id=tenant_id,
        customer_id=credit_note.customer_id,
    )

    if customer is None:
        raise ArWorkflowError("Customer not found")

    journal_lines = [
        JournalLineCreate(
            ledger_account_id=customer.revenue_account_id,
            line_number=1,
            description=credit_note.reason,
            debit=credit_note.amount,
        )
    ]

    if credit_note.tax_amount > 0:
        if customer.tax_account_id is None:
            raise ArWorkflowError(
                "Customer tax account is not configured"
            )

        journal_lines.append(
            JournalLineCreate(
                ledger_account_id=customer.tax_account_id,
                line_number=2,
                description="Reverse output tax",
                debit=credit_note.tax_amount,
            )
        )

    journal_lines.append(
        JournalLineCreate(
            ledger_account_id=customer.ar_control_account_id,
            line_number=len(journal_lines) + 1,
            description="Reduce customer receivable",
            credit=credit_note.total_amount,
        )
    )

    journal = await create_draft_journal(
        session,
        payload=JournalEntryCreate(
            tenant_id=tenant_id,
            fiscal_period_id=credit_note.fiscal_period_id,
            journal_number=(
                f"CN-{credit_note.credit_note_number}"
            ),
            entry_date=credit_note.credit_note_date,
            source=JournalSource.ACCOUNTS_RECEIVABLE,
            source_reference=str(credit_note.id),
            description=(
                f"Customer credit note "
                f"{credit_note.credit_note_number}"
            ),
            created_by=issued_by,
            lines=journal_lines,
        ),
    )

    await post_journal(
        session,
        tenant_id=tenant_id,
        journal_id=journal.id,
        posted_by=issued_by,
    )

    credit_note = await get_credit_note(
        session,
        tenant_id=tenant_id,
        credit_note_id=credit_note_id,
        for_update=True,
    )

    if credit_note is None:
        raise ArWorkflowError(
            "Credit note disappeared after posting"
        )

    credit_note.status = CreditNoteStatus.ISSUED
    credit_note.journal_entry_id = journal.id

    if credit_note.invoice_id is not None:
        invoice = await get_invoice(
            session,
            tenant_id=tenant_id,
            invoice_id=credit_note.invoice_id,
            for_update=True,
        )

        if invoice is None:
            raise ArWorkflowError("Invoice not found")

        invoice.credited_amount = quantize_money(
            invoice.credited_amount
            + credit_note.total_amount
        )
        invoice.outstanding_amount = (
            calculate_outstanding_amount(
                total_amount=invoice.total_amount,
                paid_amount=invoice.paid_amount,
                credited_amount=invoice.credited_amount,
            )
        )

        if invoice.outstanding_amount == 0:
            invoice.status = InvoiceStatus.CREDITED
        elif invoice.paid_amount > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID

        credit_note.applied_amount = (
            credit_note.total_amount
        )
        credit_note.status = CreditNoteStatus.APPLIED

    await session.commit()
    await session.refresh(credit_note)

    return credit_note


async def build_aging(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    as_of_date: date,
    customer_id: UUID | None = None,
) -> CustomerAgingRead:
    invoices = await list_outstanding_invoices(
        session,
        tenant_id=tenant_id,
        customer_id=customer_id,
        as_of_date=as_of_date,
    )

    totals = {
        "current": Decimal("0"),
        "days_1_30": Decimal("0"),
        "days_31_60": Decimal("0"),
        "days_61_90": Decimal("0"),
        "over_90": Decimal("0"),
        "total": Decimal("0"),
    }

    for invoice in invoices:
        bucket = calculate_aging_bucket(
            as_of_date=as_of_date,
            due_date=invoice.due_date,
            outstanding_amount=(
                invoice.outstanding_amount
            ),
        )

        for field in totals:
            totals[field] += getattr(bucket, field)

    return CustomerAgingRead(
        tenant_id=tenant_id,
        customer_id=customer_id,
        as_of_date=as_of_date,
        **totals,
    )
