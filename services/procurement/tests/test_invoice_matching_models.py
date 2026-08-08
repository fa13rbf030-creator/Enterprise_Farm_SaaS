from procurement_service.core.enums import (
    InvoiceMatchExceptionType,
    InvoiceMatchLineStatus,
    InvoiceMatchStatus,
)
from procurement_service.db.base import Base
from procurement_service.models import (
    SupplierInvoiceMatch,
    SupplierInvoiceMatchLine,
)


def test_invoice_match_tables_registered() -> None:
    expected = {
        "procurement_supplier_invoice_matches",
        "procurement_supplier_invoice_match_lines",
    }

    assert expected.issubset(
        Base.metadata.tables.keys()
    )


def test_invoice_match_status_values() -> None:
    assert InvoiceMatchStatus.PENDING.value == "PENDING"
    assert InvoiceMatchStatus.MATCHED.value == "MATCHED"
    assert (
        InvoiceMatchStatus.WITHIN_TOLERANCE.value
        == "WITHIN_TOLERANCE"
    )
    assert InvoiceMatchStatus.EXCEPTION.value == "EXCEPTION"
    assert InvoiceMatchStatus.HANDED_OFF.value == "HANDED_OFF"


def test_invoice_match_line_status_values() -> None:
    assert (
        InvoiceMatchLineStatus.QUANTITY_VARIANCE.value
        == "QUANTITY_VARIANCE"
    )
    assert (
        InvoiceMatchLineStatus.PRICE_VARIANCE.value
        == "PRICE_VARIANCE"
    )


def test_invoice_match_exception_values() -> None:
    assert InvoiceMatchExceptionType.NONE.value == "NONE"
    assert (
        InvoiceMatchExceptionType.DUPLICATE_INVOICE.value
        == "DUPLICATE_INVOICE"
    )


def test_invoice_match_internal_foreign_keys() -> None:
    table = SupplierInvoiceMatch.__table__

    assert table.c.supplier_id.foreign_keys
    assert table.c.purchase_order_id.foreign_keys
    assert table.c.goods_receipt_id.foreign_keys


def test_invoice_match_line_internal_foreign_keys() -> None:
    table = SupplierInvoiceMatchLine.__table__

    assert table.c.invoice_match_id.foreign_keys
    assert table.c.purchase_order_line_id.foreign_keys
    assert table.c.goods_receipt_line_id.foreign_keys


def test_finance_reference_is_not_cross_service_fk() -> None:
    column = (
        SupplierInvoiceMatch.__table__
        .c.finance_ap_invoice_id
    )

    assert len(column.foreign_keys) == 0


def test_inventory_reference_is_not_cross_service_fk() -> None:
    column = (
        SupplierInvoiceMatchLine.__table__
        .c.item_id
    )

    assert len(column.foreign_keys) == 0


def test_invoice_match_tenant_columns_required() -> None:
    assert not (
        SupplierInvoiceMatch.__table__
        .c.tenant_id.nullable
    )

    assert not (
        SupplierInvoiceMatchLine.__table__
        .c.tenant_id.nullable
    )


def test_invoice_match_table_names() -> None:
    assert (
        SupplierInvoiceMatch.__tablename__
        == "procurement_supplier_invoice_matches"
    )

    assert (
        SupplierInvoiceMatchLine.__tablename__
        == "procurement_supplier_invoice_match_lines"
    )
