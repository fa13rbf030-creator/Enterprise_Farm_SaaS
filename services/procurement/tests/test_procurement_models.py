from procurement_service.core.enums import (
    RequisitionPriority,
    RequisitionStatus,
    SupplierStatus,
)
from procurement_service.db.base import Base
from procurement_service.models import (
    ProcurementSupplier,
    PurchaseRequisition,
    PurchaseRequisitionLine,
)


def test_procurement_tables_registered() -> None:
    expected = {
        "procurement_suppliers",
        "procurement_purchase_requisitions",
        "procurement_purchase_requisition_lines",
    }

    assert expected.issubset(
        Base.metadata.tables.keys()
    )


def test_procurement_enum_values() -> None:
    assert SupplierStatus.ACTIVE.value == "ACTIVE"
    assert RequisitionStatus.SUBMITTED.value == "SUBMITTED"
    assert RequisitionPriority.URGENT.value == "URGENT"


def test_supplier_finance_link_is_not_cross_service_fk() -> None:
    table = ProcurementSupplier.__table__

    column = table.c.finance_vendor_id

    assert len(column.foreign_keys) == 0


def test_requisition_line_relations() -> None:
    table = PurchaseRequisitionLine.__table__

    assert table.c.requisition_id.foreign_keys
    assert table.c.preferred_supplier_id.foreign_keys

    assert PurchaseRequisition.__tablename__ == (
        "procurement_purchase_requisitions"
    )
