from procurement_service.core.enums import (
    QuotationStatus,
    RfqStatus,
)
from procurement_service.db.base import Base
from procurement_service.models import (
    RequestForQuotation,
    RequestForQuotationLine,
    SupplierQuotation,
    SupplierQuotationLine,
)


def test_sourcing_tables_registered() -> None:
    expected = {
        "procurement_rfqs",
        "procurement_rfq_lines",
        "procurement_supplier_quotations",
        "procurement_supplier_quotation_lines",
    }

    assert expected.issubset(
        Base.metadata.tables.keys()
    )


def test_sourcing_enum_values() -> None:
    assert RfqStatus.ISSUED.value == "ISSUED"
    assert RfqStatus.AWARDED.value == "AWARDED"
    assert QuotationStatus.SUBMITTED.value == "SUBMITTED"
    assert QuotationStatus.ACCEPTED.value == "ACCEPTED"


def test_rfq_internal_foreign_keys() -> None:
    rfq_line = RequestForQuotationLine.__table__

    assert rfq_line.c.rfq_id.foreign_keys
    assert rfq_line.c.requisition_line_id.foreign_keys


def test_quotation_internal_foreign_keys() -> None:
    quotation = SupplierQuotation.__table__
    line = SupplierQuotationLine.__table__

    assert quotation.c.rfq_id.foreign_keys
    assert quotation.c.supplier_id.foreign_keys
    assert line.c.quotation_id.foreign_keys
    assert line.c.rfq_line_id.foreign_keys


def test_sourcing_table_names() -> None:
    assert RequestForQuotation.__tablename__ == "procurement_rfqs"
    assert SupplierQuotation.__tablename__ == (
        "procurement_supplier_quotations"
    )
