from procurement_service.core.enums import (
    PurchaseOrderLineStatus,
    PurchaseOrderStatus,
)
from procurement_service.db.base import Base
from procurement_service.models import (
    PurchaseOrder,
    PurchaseOrderLine,
)


def test_purchase_order_tables_registered() -> None:
    expected = {
        "procurement_purchase_orders",
        "procurement_purchase_order_lines",
    }

    assert expected.issubset(
        Base.metadata.tables.keys()
    )


def test_purchase_order_status_values() -> None:
    assert PurchaseOrderStatus.DRAFT.value == "DRAFT"
    assert (
        PurchaseOrderStatus.PENDING_APPROVAL.value
        == "PENDING_APPROVAL"
    )
    assert (
        PurchaseOrderStatus.PARTIALLY_RECEIVED.value
        == "PARTIALLY_RECEIVED"
    )
    assert (
        PurchaseOrderStatus.FULLY_RECEIVED.value
        == "FULLY_RECEIVED"
    )


def test_purchase_order_line_status_values() -> None:
    assert PurchaseOrderLineStatus.OPEN.value == "OPEN"
    assert (
        PurchaseOrderLineStatus.PARTIALLY_RECEIVED.value
        == "PARTIALLY_RECEIVED"
    )
    assert (
        PurchaseOrderLineStatus.FULLY_RECEIVED.value
        == "FULLY_RECEIVED"
    )


def test_purchase_order_internal_foreign_keys() -> None:
    table = PurchaseOrder.__table__

    assert table.c.supplier_id.foreign_keys
    assert table.c.source_quotation_id.foreign_keys
    assert table.c.requisition_id.foreign_keys


def test_purchase_order_line_internal_foreign_keys() -> None:
    table = PurchaseOrderLine.__table__

    assert table.c.purchase_order_id.foreign_keys
    assert table.c.requisition_line_id.foreign_keys
    assert table.c.quotation_line_id.foreign_keys


def test_purchase_order_inventory_reference_not_cross_service_fk() -> None:
    column = PurchaseOrderLine.__table__.c.item_id

    assert len(column.foreign_keys) == 0


def test_purchase_order_table_names() -> None:
    assert (
        PurchaseOrder.__tablename__
        == "procurement_purchase_orders"
    )

    assert (
        PurchaseOrderLine.__tablename__
        == "procurement_purchase_order_lines"
    )


def test_purchase_order_tenant_columns_required() -> None:
    assert not PurchaseOrder.__table__.c.tenant_id.nullable
    assert not PurchaseOrderLine.__table__.c.tenant_id.nullable
