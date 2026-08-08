from procurement_service.core.enums import (
    GoodsReceiptLineStatus,
    GoodsReceiptStatus,
    InspectionStatus,
)
from procurement_service.db.base import Base
from procurement_service.models import (
    GoodsReceipt,
    GoodsReceiptLine,
)


def test_goods_receipt_tables_registered() -> None:
    expected = {
        "procurement_goods_receipts",
        "procurement_goods_receipt_lines",
    }

    assert expected.issubset(
        Base.metadata.tables.keys()
    )


def test_goods_receipt_status_values() -> None:
    assert GoodsReceiptStatus.DRAFT.value == "DRAFT"
    assert GoodsReceiptStatus.RECEIVED.value == "RECEIVED"
    assert GoodsReceiptStatus.ACCEPTED.value == "ACCEPTED"
    assert (
        GoodsReceiptStatus.PARTIALLY_ACCEPTED.value
        == "PARTIALLY_ACCEPTED"
    )
    assert GoodsReceiptStatus.REJECTED.value == "REJECTED"


def test_goods_receipt_line_status_values() -> None:
    assert GoodsReceiptLineStatus.RECEIVED.value == "RECEIVED"
    assert GoodsReceiptLineStatus.ACCEPTED.value == "ACCEPTED"
    assert (
        GoodsReceiptLineStatus.PARTIALLY_ACCEPTED.value
        == "PARTIALLY_ACCEPTED"
    )


def test_inspection_status_values() -> None:
    assert InspectionStatus.NOT_REQUIRED.value == "NOT_REQUIRED"
    assert InspectionStatus.PENDING.value == "PENDING"
    assert InspectionStatus.PASSED.value == "PASSED"
    assert InspectionStatus.FAILED.value == "FAILED"


def test_goods_receipt_foreign_keys() -> None:
    table = GoodsReceipt.__table__

    assert table.c.purchase_order_id.foreign_keys
    assert table.c.supplier_id.foreign_keys


def test_goods_receipt_line_foreign_keys() -> None:
    table = GoodsReceiptLine.__table__

    assert table.c.goods_receipt_id.foreign_keys
    assert table.c.purchase_order_line_id.foreign_keys


def test_inventory_and_warehouse_references_are_not_cross_service_fks() -> None:
    receipt = GoodsReceipt.__table__
    line = GoodsReceiptLine.__table__

    assert len(receipt.c.warehouse_id.foreign_keys) == 0
    assert len(line.c.item_id.foreign_keys) == 0
    assert len(line.c.warehouse_location_id.foreign_keys) == 0


def test_goods_receipt_tenant_columns_required() -> None:
    assert not GoodsReceipt.__table__.c.tenant_id.nullable
    assert not GoodsReceiptLine.__table__.c.tenant_id.nullable


def test_goods_receipt_table_names() -> None:
    assert (
        GoodsReceipt.__tablename__
        == "procurement_goods_receipts"
    )
    assert (
        GoodsReceiptLine.__tablename__
        == "procurement_goods_receipt_lines"
    )
