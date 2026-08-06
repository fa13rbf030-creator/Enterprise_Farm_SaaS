from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import SupplierInvoiceStatus
from finance_service.models.ap import (
    SupplierInvoice,
    SupplierInvoiceLine,
    VendorAccount,
    VendorDebitNote,
    VendorPayment,
    VendorPaymentAllocation,
)


async def get_vendor(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    vendor_id: UUID,
    for_update: bool = False,
) -> VendorAccount | None:
    query = select(VendorAccount).where(
        VendorAccount.id == vendor_id,
        VendorAccount.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_vendors(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[VendorAccount]:
    result = await session.execute(
        select(VendorAccount)
        .where(VendorAccount.tenant_id == tenant_id)
        .order_by(VendorAccount.vendor_code)
    )

    return list(result.scalars().all())


async def get_supplier_invoice(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    invoice_id: UUID,
    for_update: bool = False,
) -> SupplierInvoice | None:
    query = select(SupplierInvoice).where(
        SupplierInvoice.id == invoice_id,
        SupplierInvoice.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_supplier_invoice_lines(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    invoice_id: UUID,
) -> list[SupplierInvoiceLine]:
    result = await session.execute(
        select(SupplierInvoiceLine)
        .where(
            SupplierInvoiceLine.tenant_id == tenant_id,
            SupplierInvoiceLine.invoice_id == invoice_id,
        )
        .order_by(SupplierInvoiceLine.line_number)
    )

    return list(result.scalars().all())


async def list_vendor_invoices(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    vendor_id: UUID,
) -> list[SupplierInvoice]:
    result = await session.execute(
        select(SupplierInvoice)
        .where(
            SupplierInvoice.tenant_id == tenant_id,
            SupplierInvoice.vendor_id == vendor_id,
        )
        .order_by(
            SupplierInvoice.invoice_date.desc(),
            SupplierInvoice.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def list_outstanding_supplier_invoices(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    vendor_id: UUID | None = None,
    as_of_date: date | None = None,
) -> list[SupplierInvoice]:
    query = select(SupplierInvoice).where(
        SupplierInvoice.tenant_id == tenant_id,
        SupplierInvoice.outstanding_amount > 0,
        SupplierInvoice.status.in_(
            [
                SupplierInvoiceStatus.POSTED,
                SupplierInvoiceStatus.PARTIALLY_PAID,
            ]
        ),
    )

    if vendor_id is not None:
        query = query.where(
            SupplierInvoice.vendor_id == vendor_id
        )

    if as_of_date is not None:
        query = query.where(
            SupplierInvoice.invoice_date <= as_of_date
        )

    result = await session.execute(
        query.order_by(
            SupplierInvoice.due_date,
            SupplierInvoice.invoice_number,
        )
    )

    return list(result.scalars().all())


async def get_vendor_payment(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    payment_id: UUID,
    for_update: bool = False,
) -> VendorPayment | None:
    query = select(VendorPayment).where(
        VendorPayment.id == payment_id,
        VendorPayment.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_vendor_payment_allocation(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    payment_id: UUID,
    invoice_id: UUID,
) -> VendorPaymentAllocation | None:
    result = await session.execute(
        select(VendorPaymentAllocation).where(
            VendorPaymentAllocation.tenant_id == tenant_id,
            VendorPaymentAllocation.payment_id == payment_id,
            VendorPaymentAllocation.invoice_id == invoice_id,
        )
    )

    return result.scalar_one_or_none()


async def get_vendor_debit_note(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    debit_note_id: UUID,
    for_update: bool = False,
) -> VendorDebitNote | None:
    query = select(VendorDebitNote).where(
        VendorDebitNote.id == debit_note_id,
        VendorDebitNote.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()
