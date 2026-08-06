from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    AccountStatus,
    AccountType,
    DebitNoteStatus,
    FiscalPeriodStatus,
    JournalSource,
    SupplierInvoiceStatus,
    VendorPaymentStatus,
    VendorStatus,
)
from finance_service.models.ap import (
    SupplierInvoice,
    SupplierInvoiceLine,
    VendorAccount,
    VendorDebitNote,
    VendorPayment,
    VendorPaymentAllocation,
)
from finance_service.repositories.ap import (
    get_supplier_invoice,
    get_vendor,
    get_vendor_debit_note,
    get_vendor_payment,
    get_vendor_payment_allocation,
    list_outstanding_supplier_invoices,
    list_supplier_invoice_lines,
)
from finance_service.repositories.gl import (
    get_account,
    get_fiscal_period,
)
from finance_service.schemas.ap import (
    DebitNoteCreate,
    PayablesAgingRead,
    SupplierInvoiceCreate,
    SupplierInvoiceDetailRead,
    SupplierInvoiceLineRead,
    VendorCreate,
    VendorPaymentAllocationCreate,
    VendorPaymentCreate,
)
from finance_service.schemas.gl import (
    JournalEntryCreate,
    JournalLineCreate,
)
from finance_service.services.ap_calculations import (
    ApCalculationError,
    calculate_payable_outstanding,
    calculate_payables_aging,
    calculate_supplier_invoice_totals,
    quantize_ap_money,
)
from finance_service.services.gl import create_draft_journal
from finance_service.services.posting import post_journal


class ApWorkflowError(ValueError):
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
        raise ApWorkflowError("Fiscal period not found")

    if period.status != FiscalPeriodStatus.OPEN:
        raise ApWorkflowError(
            "AP transaction requires an open period"
        )

    if not (
        period.starts_on
        <= transaction_date
        <= period.ends_on
    ):
        raise ApWorkflowError(
            "AP transaction date is outside fiscal period"
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
        raise ApWorkflowError(
            "Ledger account not found in tenant"
        )

    if account.status != AccountStatus.ACTIVE:
        raise ApWorkflowError(
            "Ledger account is not active"
        )

    if (
        expected_type is not None
        and account.account_type != expected_type
    ):
        raise ApWorkflowError(
            f"Ledger account must be {expected_type.value}"
        )

    return account


async def create_vendor(
    session: AsyncSession,
    *,
    payload: VendorCreate,
) -> VendorAccount:
    await _require_account(
        session,
        tenant_id=payload.tenant_id,
        account_id=payload.ap_control_account_id,
        expected_type=AccountType.LIABILITY,
    )

    await _require_account(
        session,
        tenant_id=payload.tenant_id,
        account_id=payload.default_expense_account_id,
        expected_type=AccountType.EXPENSE,
    )

    if payload.input_tax_account_id is not None:
        await _require_account(
            session,
            tenant_id=payload.tenant_id,
            account_id=payload.input_tax_account_id,
            expected_type=AccountType.ASSET,
        )

    if payload.withholding_tax_account_id is not None:
        await _require_account(
            session,
            tenant_id=payload.tenant_id,
            account_id=payload.withholding_tax_account_id,
            expected_type=AccountType.LIABILITY,
        )

    vendor = VendorAccount(
        tenant_id=payload.tenant_id,
        vendor_code=payload.vendor_code.strip(),
        name=payload.name.strip(),
        email=(
            str(payload.email)
            if payload.email is not None
            else None
        ),
        phone=payload.phone,
        billing_address=payload.billing_address.strip(),
        currency_code=payload.currency_code.upper(),
        payment_terms_days=payload.payment_terms_days,
        credit_limit=payload.credit_limit,
        ap_control_account_id=payload.ap_control_account_id,
        default_expense_account_id=(
            payload.default_expense_account_id
        ),
        input_tax_account_id=payload.input_tax_account_id,
        withholding_tax_account_id=(
            payload.withholding_tax_account_id
        ),
        is_tax_registered=payload.is_tax_registered,
        tax_registration_number=(
            payload.tax_registration_number
        ),
    )

    session.add(vendor)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ApWorkflowError(
            "Vendor code already exists in tenant"
        ) from exc

    await session.refresh(vendor)
    return vendor


async def create_supplier_invoice(
    session: AsyncSession,
    *,
    payload: SupplierInvoiceCreate,
) -> SupplierInvoice:
    vendor = await get_vendor(
        session,
        tenant_id=payload.tenant_id,
        vendor_id=payload.vendor_id,
    )

    if vendor is None:
        raise ApWorkflowError("Vendor not found")

    if vendor.status != VendorStatus.ACTIVE:
        raise ApWorkflowError("Vendor is not active")

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
            withholding_total,
            total_amount,
        ) = calculate_supplier_invoice_totals(payload)
    except ApCalculationError as exc:
        raise ApWorkflowError(str(exc)) from exc

    for line in payload.lines:
        await _require_account(
            session,
            tenant_id=payload.tenant_id,
            account_id=line.expense_account_id,
            expected_type=AccountType.EXPENSE,
        )

    invoice = SupplierInvoice(
        tenant_id=payload.tenant_id,
        vendor_id=payload.vendor_id,
        fiscal_period_id=payload.fiscal_period_id,
        invoice_number=payload.invoice_number.strip(),
        vendor_reference=payload.vendor_reference,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        currency_code=payload.currency_code.upper(),
        exchange_rate=payload.exchange_rate,
        subtotal=subtotal,
        discount_total=discount_total,
        tax_total=tax_total,
        withholding_tax_total=withholding_total,
        total_amount=total_amount,
        outstanding_amount=total_amount,
        description=payload.description.strip(),
        created_by=payload.created_by,
    )

    session.add(invoice)
    await session.flush()

    for line in payload.lines:
        gross = quantize_ap_money(
            line.quantity * line.unit_price
        )
        taxable = gross - line.discount_amount
        tax_amount = quantize_ap_money(
            taxable * line.tax_rate / Decimal("100")
        )
        withholding_amount = quantize_ap_money(
            taxable
            * line.withholding_tax_rate
            / Decimal("100")
        )
        line_total = quantize_ap_money(
            taxable + tax_amount - withholding_amount
        )

        session.add(
            SupplierInvoiceLine(
                tenant_id=payload.tenant_id,
                invoice_id=invoice.id,
                line_number=line.line_number,
                description=line.description.strip(),
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_amount=line.discount_amount,
                tax_rate=line.tax_rate,
                tax_amount=tax_amount,
                withholding_tax_rate=(
                    line.withholding_tax_rate
                ),
                withholding_tax_amount=(
                    withholding_amount
                ),
                line_total=line_total,
                expense_account_id=line.expense_account_id,
            )
        )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ApWorkflowError(
            "Supplier invoice number already exists"
        ) from exc

    await session.refresh(invoice)
    return invoice


async def get_supplier_invoice_detail(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    invoice_id: UUID,
) -> SupplierInvoiceDetailRead:
    invoice = await get_supplier_invoice(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice_id,
    )

    if invoice is None:
        raise ApWorkflowError("Supplier invoice not found")

    lines = await list_supplier_invoice_lines(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice.id,
    )

    return SupplierInvoiceDetailRead(
        **invoice.__dict__,
        lines=[
            SupplierInvoiceLineRead.model_validate(line)
            for line in lines
        ],
    )


async def post_supplier_invoice(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    invoice_id: UUID,
    posted_by: UUID,
) -> SupplierInvoice:
    invoice = await get_supplier_invoice(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        for_update=True,
    )

    if invoice is None:
        raise ApWorkflowError("Supplier invoice not found")

    if invoice.status != SupplierInvoiceStatus.DRAFT:
        raise ApWorkflowError(
            "Only draft supplier invoices can be posted"
        )

    vendor = await get_vendor(
        session,
        tenant_id=tenant_id,
        vendor_id=invoice.vendor_id,
    )

    if vendor is None:
        raise ApWorkflowError("Vendor not found")

    lines = await list_supplier_invoice_lines(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice.id,
    )

    journal_lines: list[JournalLineCreate] = []
    line_number = 1

    for line in lines:
        expense_amount = quantize_ap_money(
            line.line_total
            - line.tax_amount
            + line.withholding_tax_amount
        )

        journal_lines.append(
            JournalLineCreate(
                ledger_account_id=line.expense_account_id,
                line_number=line_number,
                description=line.description,
                debit=expense_amount,
            )
        )
        line_number += 1

    if invoice.tax_total > 0:
        if vendor.input_tax_account_id is None:
            raise ApWorkflowError(
                "Vendor input-tax account is not configured"
            )

        journal_lines.append(
            JournalLineCreate(
                ledger_account_id=vendor.input_tax_account_id,
                line_number=line_number,
                description="Input tax",
                debit=invoice.tax_total,
            )
        )
        line_number += 1

    if invoice.withholding_tax_total > 0:
        if vendor.withholding_tax_account_id is None:
            raise ApWorkflowError(
                "Vendor withholding-tax account "
                "is not configured"
            )

        journal_lines.append(
            JournalLineCreate(
                ledger_account_id=(
                    vendor.withholding_tax_account_id
                ),
                line_number=line_number,
                description="Withholding tax payable",
                credit=invoice.withholding_tax_total,
            )
        )
        line_number += 1

    journal_lines.append(
        JournalLineCreate(
            ledger_account_id=vendor.ap_control_account_id,
            line_number=line_number,
            description=(
                f"Supplier invoice {invoice.invoice_number}"
            ),
            credit=invoice.total_amount,
        )
    )

    journal = await create_draft_journal(
        session,
        payload=JournalEntryCreate(
            tenant_id=tenant_id,
            fiscal_period_id=invoice.fiscal_period_id,
            journal_number=f"AP-{invoice.invoice_number}",
            entry_date=invoice.invoice_date,
            source=JournalSource.ACCOUNTS_PAYABLE,
            source_reference=str(invoice.id),
            description=(
                f"Supplier invoice {invoice.invoice_number}"
            ),
            created_by=posted_by,
            lines=journal_lines,
        ),
    )

    await post_journal(
        session,
        tenant_id=tenant_id,
        journal_id=journal.id,
        posted_by=posted_by,
    )

    invoice = await get_supplier_invoice(
        session,
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        for_update=True,
    )

    if invoice is None:
        raise ApWorkflowError(
            "Supplier invoice disappeared after posting"
        )

    invoice.status = SupplierInvoiceStatus.POSTED
    invoice.journal_entry_id = journal.id
    invoice.posted_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(invoice)

    return invoice


async def create_vendor_payment(
    session: AsyncSession,
    *,
    payload: VendorPaymentCreate,
) -> VendorPayment:
    vendor = await get_vendor(
        session,
        tenant_id=payload.tenant_id,
        vendor_id=payload.vendor_id,
    )

    if vendor is None:
        raise ApWorkflowError("Vendor not found")

    await _require_open_period(
        session,
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
        transaction_date=payload.payment_date,
    )

    await _require_account(
        session,
        tenant_id=payload.tenant_id,
        account_id=payload.cash_account_id,
        expected_type=AccountType.ASSET,
    )

    payment = VendorPayment(
        tenant_id=payload.tenant_id,
        vendor_id=payload.vendor_id,
        fiscal_period_id=payload.fiscal_period_id,
        payment_number=payload.payment_number.strip(),
        payment_date=payload.payment_date,
        amount=payload.amount,
        allocated_amount=Decimal("0"),
        unallocated_amount=payload.amount,
        currency_code=payload.currency_code.upper(),
        exchange_rate=payload.exchange_rate,
        payment_method=payload.payment_method,
        reference_number=payload.reference_number,
        cash_account_id=payload.cash_account_id,
        created_by=payload.created_by,
    )

    session.add(payment)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ApWorkflowError(
            "Vendor payment number already exists"
        ) from exc

    await session.refresh(payment)
    return payment


async def post_vendor_payment(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    payment_id: UUID,
    posted_by: UUID,
) -> VendorPayment:
    payment = await get_vendor_payment(
        session,
        tenant_id=tenant_id,
        payment_id=payment_id,
        for_update=True,
    )

    if payment is None:
        raise ApWorkflowError("Vendor payment not found")

    if payment.status != VendorPaymentStatus.DRAFT:
        raise ApWorkflowError(
            "Only draft vendor payments can be posted"
        )

    vendor = await get_vendor(
        session,
        tenant_id=tenant_id,
        vendor_id=payment.vendor_id,
    )

    if vendor is None:
        raise ApWorkflowError("Vendor not found")

    journal = await create_draft_journal(
        session,
        payload=JournalEntryCreate(
            tenant_id=tenant_id,
            fiscal_period_id=payment.fiscal_period_id,
            journal_number=f"PAY-{payment.payment_number}",
            entry_date=payment.payment_date,
            source=JournalSource.ACCOUNTS_PAYABLE,
            source_reference=str(payment.id),
            description=(
                f"Vendor payment {payment.payment_number}"
            ),
            created_by=posted_by,
            lines=[
                JournalLineCreate(
                    ledger_account_id=(
                        vendor.ap_control_account_id
                    ),
                    line_number=1,
                    description="Reduce supplier payable",
                    debit=payment.amount,
                ),
                JournalLineCreate(
                    ledger_account_id=payment.cash_account_id,
                    line_number=2,
                    description="Cash/bank payment",
                    credit=payment.amount,
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

    payment = await get_vendor_payment(
        session,
        tenant_id=tenant_id,
        payment_id=payment_id,
        for_update=True,
    )

    if payment is None:
        raise ApWorkflowError(
            "Vendor payment disappeared after posting"
        )

    payment.status = VendorPaymentStatus.POSTED
    payment.journal_entry_id = journal.id

    await session.commit()
    await session.refresh(payment)

    return payment


async def allocate_vendor_payment(
    session: AsyncSession,
    *,
    payment_id: UUID,
    payload: VendorPaymentAllocationCreate,
) -> VendorPayment:
    payment = await get_vendor_payment(
        session,
        tenant_id=payload.tenant_id,
        payment_id=payment_id,
        for_update=True,
    )

    if payment is None:
        raise ApWorkflowError("Vendor payment not found")

    if payment.status not in {
        VendorPaymentStatus.POSTED,
        VendorPaymentStatus.PARTIALLY_ALLOCATED,
    }:
        raise ApWorkflowError(
            "Vendor payment must be posted before allocation"
        )

    invoice = await get_supplier_invoice(
        session,
        tenant_id=payload.tenant_id,
        invoice_id=payload.invoice_id,
        for_update=True,
    )

    if invoice is None:
        raise ApWorkflowError("Supplier invoice not found")

    if invoice.vendor_id != payment.vendor_id:
        raise ApWorkflowError(
            "Payment and invoice vendors differ"
        )

    if payload.allocated_amount > payment.unallocated_amount:
        raise ApWorkflowError(
            "Allocation exceeds unallocated payment amount"
        )

    if payload.allocated_amount > invoice.outstanding_amount:
        raise ApWorkflowError(
            "Allocation exceeds invoice outstanding amount"
        )

    existing = await get_vendor_payment_allocation(
        session,
        tenant_id=payload.tenant_id,
        payment_id=payment.id,
        invoice_id=invoice.id,
    )

    if existing is not None:
        raise ApWorkflowError(
            "Payment is already allocated to invoice"
        )

    session.add(
        VendorPaymentAllocation(
            tenant_id=payload.tenant_id,
            payment_id=payment.id,
            invoice_id=invoice.id,
            allocated_amount=payload.allocated_amount,
            allocated_by=payload.allocated_by,
        )
    )

    payment.allocated_amount = quantize_ap_money(
        payment.allocated_amount + payload.allocated_amount
    )
    payment.unallocated_amount = quantize_ap_money(
        payment.amount - payment.allocated_amount
    )

    invoice.paid_amount = quantize_ap_money(
        invoice.paid_amount + payload.allocated_amount
    )
    invoice.outstanding_amount = (
        calculate_payable_outstanding(
            total_amount=invoice.total_amount,
            paid_amount=invoice.paid_amount,
            debited_amount=invoice.debited_amount,
        )
    )

    invoice.status = (
        SupplierInvoiceStatus.PAID
        if invoice.outstanding_amount == 0
        else SupplierInvoiceStatus.PARTIALLY_PAID
    )

    payment.status = (
        VendorPaymentStatus.ALLOCATED
        if payment.unallocated_amount == 0
        else VendorPaymentStatus.PARTIALLY_ALLOCATED
    )

    await session.commit()
    await session.refresh(payment)

    return payment


async def create_debit_note(
    session: AsyncSession,
    *,
    payload: DebitNoteCreate,
) -> VendorDebitNote:
    vendor = await get_vendor(
        session,
        tenant_id=payload.tenant_id,
        vendor_id=payload.vendor_id,
    )

    if vendor is None:
        raise ApWorkflowError("Vendor not found")

    await _require_open_period(
        session,
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
        transaction_date=payload.debit_note_date,
    )

    if payload.invoice_id is not None:
        invoice = await get_supplier_invoice(
            session,
            tenant_id=payload.tenant_id,
            invoice_id=payload.invoice_id,
        )

        if invoice is None:
            raise ApWorkflowError(
                "Supplier invoice not found"
            )

        if invoice.vendor_id != payload.vendor_id:
            raise ApWorkflowError(
                "Debit-note vendor does not match invoice"
            )

        if (
            payload.amount + payload.tax_amount
            > invoice.outstanding_amount
        ):
            raise ApWorkflowError(
                "Debit note exceeds invoice outstanding amount"
            )

    debit_note = VendorDebitNote(
        tenant_id=payload.tenant_id,
        vendor_id=payload.vendor_id,
        invoice_id=payload.invoice_id,
        fiscal_period_id=payload.fiscal_period_id,
        debit_note_number=(
            payload.debit_note_number.strip()
        ),
        debit_note_date=payload.debit_note_date,
        amount=payload.amount,
        tax_amount=payload.tax_amount,
        total_amount=quantize_ap_money(
            payload.amount + payload.tax_amount
        ),
        reason=payload.reason.strip(),
        created_by=payload.created_by,
    )

    session.add(debit_note)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ApWorkflowError(
            "Debit-note number already exists"
        ) from exc

    await session.refresh(debit_note)
    return debit_note


async def issue_debit_note(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    debit_note_id: UUID,
    issued_by: UUID,
) -> VendorDebitNote:
    debit_note = await get_vendor_debit_note(
        session,
        tenant_id=tenant_id,
        debit_note_id=debit_note_id,
        for_update=True,
    )

    if debit_note is None:
        raise ApWorkflowError("Debit note not found")

    if debit_note.status != DebitNoteStatus.DRAFT:
        raise ApWorkflowError(
            "Only draft debit notes can be issued"
        )

    vendor = await get_vendor(
        session,
        tenant_id=tenant_id,
        vendor_id=debit_note.vendor_id,
    )

    if vendor is None:
        raise ApWorkflowError("Vendor not found")

    journal_lines = [
        JournalLineCreate(
            ledger_account_id=vendor.ap_control_account_id,
            line_number=1,
            description="Reduce supplier payable",
            debit=debit_note.total_amount,
        ),
        JournalLineCreate(
            ledger_account_id=vendor.default_expense_account_id,
            line_number=2,
            description=debit_note.reason,
            credit=debit_note.amount,
        ),
    ]

    if debit_note.tax_amount > 0:
        if vendor.input_tax_account_id is None:
            raise ApWorkflowError(
                "Vendor input-tax account is not configured"
            )

        journal_lines.append(
            JournalLineCreate(
                ledger_account_id=vendor.input_tax_account_id,
                line_number=3,
                description="Reverse input tax",
                credit=debit_note.tax_amount,
            )
        )

    journal = await create_draft_journal(
        session,
        payload=JournalEntryCreate(
            tenant_id=tenant_id,
            fiscal_period_id=debit_note.fiscal_period_id,
            journal_number=(
                f"DN-{debit_note.debit_note_number}"
            ),
            entry_date=debit_note.debit_note_date,
            source=JournalSource.ACCOUNTS_PAYABLE,
            source_reference=str(debit_note.id),
            description=(
                f"Vendor debit note "
                f"{debit_note.debit_note_number}"
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

    debit_note = await get_vendor_debit_note(
        session,
        tenant_id=tenant_id,
        debit_note_id=debit_note_id,
        for_update=True,
    )

    if debit_note is None:
        raise ApWorkflowError(
            "Debit note disappeared after posting"
        )

    debit_note.status = DebitNoteStatus.ISSUED
    debit_note.journal_entry_id = journal.id

    if debit_note.invoice_id is not None:
        invoice = await get_supplier_invoice(
            session,
            tenant_id=tenant_id,
            invoice_id=debit_note.invoice_id,
            for_update=True,
        )

        if invoice is None:
            raise ApWorkflowError(
                "Supplier invoice not found"
            )

        invoice.debited_amount = quantize_ap_money(
            invoice.debited_amount + debit_note.total_amount
        )
        invoice.outstanding_amount = (
            calculate_payable_outstanding(
                total_amount=invoice.total_amount,
                paid_amount=invoice.paid_amount,
                debited_amount=invoice.debited_amount,
            )
        )

        if invoice.outstanding_amount == 0:
            invoice.status = SupplierInvoiceStatus.DEBITED
        elif invoice.paid_amount > 0:
            invoice.status = (
                SupplierInvoiceStatus.PARTIALLY_PAID
            )

        debit_note.applied_amount = debit_note.total_amount
        debit_note.status = DebitNoteStatus.APPLIED

    await session.commit()
    await session.refresh(debit_note)

    return debit_note


async def build_payables_aging(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    as_of_date: date,
    vendor_id: UUID | None = None,
) -> PayablesAgingRead:
    invoices = await list_outstanding_supplier_invoices(
        session,
        tenant_id=tenant_id,
        vendor_id=vendor_id,
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
        aging = calculate_payables_aging(
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            as_of_date=as_of_date,
            due_date=invoice.due_date,
            outstanding_amount=invoice.outstanding_amount,
        )

        for field in totals:
            totals[field] += getattr(aging, field)

    return PayablesAgingRead(
        tenant_id=tenant_id,
        vendor_id=vendor_id,
        as_of_date=as_of_date,
        **totals,
    )
