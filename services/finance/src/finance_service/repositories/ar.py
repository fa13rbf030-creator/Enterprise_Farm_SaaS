from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    InvoiceStatus,
)
from finance_service.models.ar import (
    CustomerAccount,
    CustomerCreditNote,
    CustomerInvoice,
    CustomerInvoiceLine,
    CustomerReceipt,
    ReceiptAllocation,
)


async def get_customer(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    customer_id: UUID,
    for_update: bool = False,
) -> CustomerAccount | None:
    query = select(CustomerAccount).where(
        CustomerAccount.id == customer_id,
        CustomerAccount.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_customers(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[CustomerAccount]:
    result = await session.execute(
        select(CustomerAccount)
        .where(CustomerAccount.tenant_id == tenant_id)
        .order_by(CustomerAccount.customer_code)
    )

    return list(result.scalars().all())


async def get_invoice(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    invoice_id: UUID,
    for_update: bool = False,
) -> CustomerInvoice | None:
    query = select(CustomerInvoice).where(
        CustomerInvoice.id == invoice_id,
        CustomerInvoice.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_invoice_lines(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    invoice_id: UUID,
) -> list[CustomerInvoiceLine]:
    result = await session.execute(
        select(CustomerInvoiceLine)
        .where(
            CustomerInvoiceLine.tenant_id == tenant_id,
            CustomerInvoiceLine.invoice_id == invoice_id,
        )
        .order_by(CustomerInvoiceLine.line_number)
    )

    return list(result.scalars().all())


async def list_customer_invoices(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    customer_id: UUID,
) -> list[CustomerInvoice]:
    result = await session.execute(
        select(CustomerInvoice)
        .where(
            CustomerInvoice.tenant_id == tenant_id,
            CustomerInvoice.customer_id == customer_id,
        )
        .order_by(
            CustomerInvoice.invoice_date.desc(),
            CustomerInvoice.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def list_outstanding_invoices(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    customer_id: UUID | None = None,
    as_of_date: date | None = None,
) -> list[CustomerInvoice]:
    query = select(CustomerInvoice).where(
        CustomerInvoice.tenant_id == tenant_id,
        CustomerInvoice.outstanding_amount > 0,
        CustomerInvoice.status.in_(
            [
                InvoiceStatus.ISSUED,
                InvoiceStatus.PARTIALLY_PAID,
            ]
        ),
    )

    if customer_id is not None:
        query = query.where(
            CustomerInvoice.customer_id == customer_id
        )

    if as_of_date is not None:
        query = query.where(
            CustomerInvoice.invoice_date <= as_of_date
        )

    result = await session.execute(
        query.order_by(
            CustomerInvoice.due_date,
            CustomerInvoice.invoice_number,
        )
    )

    return list(result.scalars().all())


async def get_receipt(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    receipt_id: UUID,
    for_update: bool = False,
) -> CustomerReceipt | None:
    query = select(CustomerReceipt).where(
        CustomerReceipt.id == receipt_id,
        CustomerReceipt.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_receipt_allocation(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    receipt_id: UUID,
    invoice_id: UUID,
) -> ReceiptAllocation | None:
    result = await session.execute(
        select(ReceiptAllocation).where(
            ReceiptAllocation.tenant_id == tenant_id,
            ReceiptAllocation.receipt_id == receipt_id,
            ReceiptAllocation.invoice_id == invoice_id,
        )
    )

    return result.scalar_one_or_none()


async def get_credit_note(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    credit_note_id: UUID,
    for_update: bool = False,
) -> CustomerCreditNote | None:
    query = select(CustomerCreditNote).where(
        CustomerCreditNote.id == credit_note_id,
        CustomerCreditNote.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()
