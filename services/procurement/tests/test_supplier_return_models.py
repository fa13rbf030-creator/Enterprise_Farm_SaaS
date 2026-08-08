from procurement_service.core.enums import (
    SupplierClaimStatus,
    SupplierReturnLineStatus,
    SupplierReturnReason,
    SupplierReturnStatus,
)
from procurement_service.db.base import Base
from procurement_service.models import (
    SupplierReturn,
    SupplierReturnLine,
)


def test_supplier_return_tables_registered() -> None:
    expected = {
        "procurement_supplier_returns",
        "procurement_supplier_return_lines",
    }

    assert expected.issubset(
        Base.metadata.tables.keys()
    )


def test_supplier_return_status_values() -> None:
    assert SupplierReturnStatus.DRAFT.value == "DRAFT"
    assert (
        SupplierReturnStatus.AUTHORIZED.value
        == "AUTHORIZED"
    )
    assert (
        SupplierReturnStatus.DISPATCHED.value
        == "DISPATCHED"
    )
    assert SupplierReturnStatus.SETTLED.value == "SETTLED"


def test_supplier_return_line_status_values() -> None:
    assert (
        SupplierReturnLineStatus.PENDING.value
        == "PENDING"
    )
    assert (
        SupplierReturnLineStatus.RECEIVED_BY_SUPPLIER.value
        == "RECEIVED_BY_SUPPLIER"
    )


def test_supplier_return_reason_values() -> None:
    assert SupplierReturnReason.DAMAGED.value == "DAMAGED"
    assert (
        SupplierReturnReason.QUALITY_FAILURE.value
        == "QUALITY_FAILURE"
    )
    assert (
        SupplierReturnReason.RECALL.value
        == "RECALL"
    )


def test_supplier_claim_status_values() -> None:
    assert (
        SupplierClaimStatus.NOT_REQUIRED.value
        == "NOT_REQUIRED"
    )
    assert SupplierClaimStatus.OPEN.value == "OPEN"
    assert SupplierClaimStatus.SETTLED.value == "SETTLED"


def test_supplier_return_internal_foreign_keys() -> None:
    table = SupplierReturn.__table__

    assert table.c.supplier_id.foreign_keys
    assert table.c.purchase_order_id.foreign_keys
    assert table.c.goods_receipt_id.foreign_keys
    assert table.c.invoice_match_id.foreign_keys


def test_supplier_return_line_internal_foreign_keys() -> None:
    table = SupplierReturnLine.__table__

    assert table.c.supplier_return_id.foreign_keys
    assert table.c.goods_receipt_line_id.foreign_keys
    assert table.c.purchase_order_line_id.foreign_keys


def test_finance_adjustment_reference_is_cross_service_safe() -> None:
    column = (
        SupplierReturn.__table__
        .c.finance_ap_adjustment_id
    )

    assert len(column.foreign_keys) == 0


def test_inventory_warehouse_logistics_quality_refs_are_not_db_fks() -> None:
    header = SupplierReturn.__table__
    line = SupplierReturnLine.__table__

    assert len(header.c.warehouse_id.foreign_keys) == 0
    assert len(header.c.shipment_id.foreign_keys) == 0
    assert len(line.c.item_id.foreign_keys) == 0
    assert len(line.c.quality_case_id.foreign_keys) == 0


def test_supplier_return_tenant_columns_required() -> None:
    assert not SupplierReturn.__table__.c.tenant_id.nullable
    assert not (
        SupplierReturnLine.__table__
        .c.tenant_id.nullable
    )


def test_supplier_return_table_names() -> None:
    assert (
        SupplierReturn.__tablename__
        == "procurement_supplier_returns"
    )

    assert (
        SupplierReturnLine.__tablename__
        == "procurement_supplier_return_lines"
    )
