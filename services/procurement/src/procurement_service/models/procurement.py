from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from procurement_service.core.enums import (
    SupplierReturnStatus,
    SupplierReturnReason,
    SupplierReturnLineStatus,
    SupplierClaimStatus,
    InvoiceMatchStatus,
    InvoiceMatchLineStatus,
    InvoiceMatchExceptionType,
    GoodsReceiptLineStatus,
    GoodsReceiptStatus,
    InspectionStatus,
    PurchaseOrderLineStatus,
    PurchaseOrderStatus,
    QuotationStatus,
    RequisitionPriority,
    RequisitionStatus,
    RfqStatus,
    SupplierStatus,
)
from procurement_service.db.base import Base


class ProcurementSupplier(Base):
    __tablename__ = "procurement_suppliers"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "supplier_code",
            name="uq_procurement_supplier_code",
        ),
        Index(
            "ix_procurement_supplier_tenant_status",
            "tenant_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    supplier_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    legal_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    finance_vendor_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment=(
            "Reference to Finance vendor representation; "
            "not a database FK across service ownership."
        ),
    )

    tax_identifier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[SupplierStatus] = mapped_column(
        Enum(
            SupplierStatus,
            name="procurement_supplier_status",
        ),
        nullable=False,
        default=SupplierStatus.DRAFT,
    )

    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class PurchaseRequisition(Base):
    __tablename__ = "procurement_purchase_requisitions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "requisition_number",
            name="uq_procurement_requisition_number",
        ),
        Index(
            "ix_procurement_requisition_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_procurement_requisition_required_date",
            "tenant_id",
            "required_by_date",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    requisition_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    requester_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    cost_centre_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Finance cost centre.",
    )

    purpose: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    required_by_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    priority: Mapped[RequisitionPriority] = mapped_column(
        Enum(
            RequisitionPriority,
            name="procurement_requisition_priority",
        ),
        nullable=False,
        default=RequisitionPriority.NORMAL,
    )
    status: Mapped[RequisitionStatus] = mapped_column(
        Enum(
            RequisitionStatus,
            name="procurement_requisition_status",
        ),
        nullable=False,
        default=RequisitionStatus.DRAFT,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    lines: Mapped[list["PurchaseRequisitionLine"]] = relationship(
        back_populates="requisition",
        cascade="all, delete-orphan",
    )


class PurchaseRequisitionLine(Base):
    __tablename__ = "procurement_purchase_requisition_lines"

    __table_args__ = (
        UniqueConstraint(
            "requisition_id",
            "line_number",
            name="uq_procurement_requisition_line_number",
        ),
        CheckConstraint(
            "quantity > 0",
            name="qty_positive",
        ),
        CheckConstraint(
            "estimated_unit_price >= 0",
            name="price_nonnegative",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    requisition_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_purchase_requisitions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to future Inventory item master.",
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    estimated_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )

    preferred_supplier_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_suppliers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    requisition: Mapped[PurchaseRequisition] = relationship(
        back_populates="lines",
    )


class RequestForQuotation(Base):
    __tablename__ = "procurement_rfqs"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "rfq_number",
            name="uq_procurement_rfq_number",
        ),
        Index(
            "ix_procurement_rfq_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_procurement_rfq_tenant_closing",
            "tenant_id",
            "closing_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    rfq_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    requisition_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_purchase_requisitions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    issue_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    closing_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    status: Mapped["RfqStatus"] = mapped_column(
        Enum(
            "DRAFT",
            "ISSUED",
            "CLOSED",
            "CANCELLED",
            "AWARDED",
            name="procurement_rfq_status",
        ),
        nullable=False,
        default="DRAFT",
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    lines: Mapped[list["RequestForQuotationLine"]] = relationship(
        back_populates="rfq",
        cascade="all, delete-orphan",
    )
    quotations: Mapped[list["SupplierQuotation"]] = relationship(
        back_populates="rfq",
    )


class RequestForQuotationLine(Base):
    __tablename__ = "procurement_rfq_lines"

    __table_args__ = (
        UniqueConstraint(
            "rfq_id",
            "line_number",
            name="uq_procurement_rfq_line_number",
        ),
        CheckConstraint(
            "quantity > 0",
            name="rfq_qty_positive",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    rfq_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_rfqs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    requisition_line_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_purchase_requisition_lines.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    rfq: Mapped[RequestForQuotation] = relationship(
        back_populates="lines",
    )


class SupplierQuotation(Base):
    __tablename__ = "procurement_supplier_quotations"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "quotation_number",
            name="uq_procurement_supplier_quotation_number",
        ),
        UniqueConstraint(
            "rfq_id",
            "supplier_id",
            name="uq_procurement_rfq_supplier_quotation",
        ),
        Index(
            "ix_procurement_quotation_tenant_status",
            "tenant_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    rfq_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_rfqs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    quotation_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    quotation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    valid_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    payment_terms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    delivery_terms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped["QuotationStatus"] = mapped_column(
        Enum(
            "DRAFT",
            "SUBMITTED",
            "UNDER_EVALUATION",
            "ACCEPTED",
            "REJECTED",
            "WITHDRAWN",
            name="procurement_quotation_status",
        ),
        nullable=False,
        default="DRAFT",
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    rfq: Mapped[RequestForQuotation] = relationship(
        back_populates="quotations",
    )
    lines: Mapped[list["SupplierQuotationLine"]] = relationship(
        back_populates="quotation",
        cascade="all, delete-orphan",
    )


class SupplierQuotationLine(Base):
    __tablename__ = "procurement_supplier_quotation_lines"

    __table_args__ = (
        UniqueConstraint(
            "quotation_id",
            "rfq_line_id",
            name="uq_procurement_quotation_rfq_line",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="quote_price_nonnegative",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    quotation_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_supplier_quotations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    rfq_line_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_rfq_lines.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    offered_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 6),
        nullable=True,
    )
    lead_time_days: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    quotation: Mapped[SupplierQuotation] = relationship(
        back_populates="lines",
    )


class PurchaseOrder(Base):
    __tablename__ = "procurement_purchase_orders"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "po_number",
            name="uq_procurement_po_number",
        ),
        Index(
            "ix_procurement_po_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_procurement_po_tenant_supplier",
            "tenant_id",
            "supplier_id",
        ),
        CheckConstraint(
            "subtotal_amount >= 0",
            name="po_subtotal_nonnegative",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="po_discount_nonnegative",
        ),
        CheckConstraint(
            "tax_amount >= 0",
            name="po_tax_nonnegative",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="po_total_nonnegative",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    source_quotation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_supplier_quotations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    requisition_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_purchase_requisitions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )

    subtotal_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    payment_terms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    delivery_terms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    delivery_location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(
            PurchaseOrderStatus,
            name="procurement_purchase_order_status",
        ),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
    )

    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )


class PurchaseOrderLine(Base):
    __tablename__ = "procurement_purchase_order_lines"

    __table_args__ = (
        UniqueConstraint(
            "purchase_order_id",
            "line_number",
            name="uq_procurement_po_line_number",
        ),
        CheckConstraint(
            "ordered_quantity > 0",
            name="po_line_qty_positive",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="po_line_price_nonnegative",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="po_line_disc_nonneg",
        ),
        CheckConstraint(
            "tax_amount >= 0",
            name="po_line_tax_nonnegative",
        ),
        CheckConstraint(
            "line_total >= 0",
            name="po_line_total_nonnegative",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_purchase_orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    requisition_line_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_purchase_requisition_lines.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    quotation_line_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_supplier_quotation_lines.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Inventory item master.",
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    ordered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    unit_of_measure: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    line_total: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    status: Mapped[PurchaseOrderLineStatus] = mapped_column(
        Enum(
            PurchaseOrderLineStatus,
            name="procurement_purchase_order_line_status",
        ),
        nullable=False,
        default=PurchaseOrderLineStatus.OPEN,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    purchase_order: Mapped[PurchaseOrder] = relationship(
        back_populates="lines",
    )


class GoodsReceipt(Base):
    __tablename__ = "procurement_goods_receipts"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "receipt_number",
            name="uq_procurement_goods_receipt_number",
        ),
        Index(
            "ix_procurement_receipt_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_procurement_receipt_tenant_po",
            "tenant_id",
            "purchase_order_id",
        ),
        Index(
            "ix_procurement_receipt_tenant_supplier",
            "tenant_id",
            "supplier_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    receipt_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_purchase_orders.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    received_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    warehouse_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Warehouse service.",
    )

    delivery_note_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    supplier_invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[GoodsReceiptStatus] = mapped_column(
        Enum(
            GoodsReceiptStatus,
            name="procurement_goods_receipt_status",
        ),
        nullable=False,
        default=GoodsReceiptStatus.DRAFT,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    lines: Mapped[list["GoodsReceiptLine"]] = relationship(
        back_populates="goods_receipt",
        cascade="all, delete-orphan",
    )


class GoodsReceiptLine(Base):
    __tablename__ = "procurement_goods_receipt_lines"

    __table_args__ = (
        UniqueConstraint(
            "goods_receipt_id",
            "line_number",
            name="uq_procurement_receipt_line_number",
        ),
        CheckConstraint(
            "received_quantity > 0",
            name="receipt_qty_positive",
        ),
        CheckConstraint(
            "accepted_quantity >= 0",
            name="receipt_accept_nonnegative",
        ),
        CheckConstraint(
            "rejected_quantity >= 0",
            name="receipt_reject_nonnegative",
        ),
        CheckConstraint(
            "accepted_quantity + rejected_quantity <= received_quantity",
            name="receipt_disposition_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    goods_receipt_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_goods_receipts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    purchase_order_line_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_purchase_order_lines.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Inventory item master.",
    )

    warehouse_location_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Warehouse storage location.",
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    accepted_quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    rejected_quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    unit_of_measure: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    lot_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    batch_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    inspection_status: Mapped[InspectionStatus] = mapped_column(
        Enum(
            InspectionStatus,
            name="procurement_receipt_inspection_status",
        ),
        nullable=False,
        default=InspectionStatus.NOT_REQUIRED,
    )

    status: Mapped[GoodsReceiptLineStatus] = mapped_column(
        Enum(
            GoodsReceiptLineStatus,
            name="procurement_goods_receipt_line_status",
        ),
        nullable=False,
        default=GoodsReceiptLineStatus.RECEIVED,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    goods_receipt: Mapped[GoodsReceipt] = relationship(
        back_populates="lines",
    )


class SupplierInvoiceMatch(Base):
    __tablename__ = "procurement_supplier_invoice_matches"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "supplier_id",
            "supplier_invoice_number",
            name="uq_procurement_invoice_match_supplier_invoice",
        ),
        Index(
            "ix_procurement_match_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_procurement_match_tenant_po",
            "tenant_id",
            "purchase_order_id",
        ),
        Index(
            "ix_procurement_match_tenant_supplier",
            "tenant_id",
            "supplier_id",
        ),
        CheckConstraint(
            "invoice_subtotal >= 0",
            name="inv_subtotal_nonneg",
        ),
        CheckConstraint(
            "invoice_tax_amount >= 0",
            name="match_tax_nonnegative",
        ),
        CheckConstraint(
            "invoice_total >= 0",
            name="match_total_nonnegative",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_purchase_orders.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    goods_receipt_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_goods_receipts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    supplier_invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    supplier_invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )

    invoice_subtotal: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    invoice_tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    invoice_total: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    quantity_tolerance_percent: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
        default=Decimal("0"),
    )

    price_tolerance_percent: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
        default=Decimal("0"),
    )

    tax_tolerance_percent: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
        default=Decimal("0"),
    )

    status: Mapped[InvoiceMatchStatus] = mapped_column(
        Enum(
            InvoiceMatchStatus,
            name="procurement_invoice_match_status",
        ),
        nullable=False,
        default=InvoiceMatchStatus.PENDING,
    )

    exception_type: Mapped[InvoiceMatchExceptionType] = mapped_column(
        Enum(
            InvoiceMatchExceptionType,
            name="procurement_invoice_match_exception_type",
        ),
        nullable=False,
        default=InvoiceMatchExceptionType.NONE,
    )

    matched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finance_ap_invoice_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment=(
            "Reference to Finance/AP invoice after "
            "successful procurement handoff."
        ),
    )

    finance_handoff_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    dispute_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    lines: Mapped[list["SupplierInvoiceMatchLine"]] = relationship(
        back_populates="invoice_match",
        cascade="all, delete-orphan",
    )


class SupplierInvoiceMatchLine(Base):
    __tablename__ = "procurement_supplier_invoice_match_lines"

    __table_args__ = (
        UniqueConstraint(
            "invoice_match_id",
            "line_number",
            name="uq_procurement_invoice_match_line_number",
        ),
        CheckConstraint(
            "invoiced_quantity > 0",
            name="inv_line_qty_pos",
        ),
        CheckConstraint(
            "invoiced_unit_price >= 0",
            name="inv_ln_price_nonneg",
        ),
        CheckConstraint(
            "invoiced_tax_amount >= 0",
            name="inv_line_tax_nonneg",
        ),
        CheckConstraint(
            "invoiced_line_total >= 0",
            name="inv_ln_total_nonneg",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    invoice_match_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_supplier_invoice_matches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    purchase_order_line_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_purchase_order_lines.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    goods_receipt_line_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_goods_receipt_lines.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Inventory item master.",
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    invoiced_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    invoiced_tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    invoiced_line_total: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    po_quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    po_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    quantity_variance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    price_variance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    tax_variance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    status: Mapped[InvoiceMatchLineStatus] = mapped_column(
        Enum(
            InvoiceMatchLineStatus,
            name="procurement_invoice_match_line_status",
        ),
        nullable=False,
        default=InvoiceMatchLineStatus.MATCHED,
    )

    exception_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    invoice_match: Mapped[SupplierInvoiceMatch] = relationship(
        back_populates="lines",
    )


class SupplierReturn(Base):
    __tablename__ = "procurement_supplier_returns"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "return_number",
            name="uq_procurement_supplier_return_number",
        ),
        Index(
            "ix_procurement_return_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_procurement_return_tenant_supplier",
            "tenant_id",
            "supplier_id",
        ),
        Index(
            "ix_procurement_return_tenant_receipt",
            "tenant_id",
            "goods_receipt_id",
        ),
        CheckConstraint(
            "estimated_return_value >= 0",
            name="return_value_nonneg",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    return_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_purchase_orders.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    goods_receipt_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_goods_receipts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    invoice_match_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "procurement_supplier_invoice_matches.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    status: Mapped[SupplierReturnStatus] = mapped_column(
        Enum(
            SupplierReturnStatus,
            name="procurement_supplier_return_status",
        ),
        nullable=False,
        default=SupplierReturnStatus.DRAFT,
    )

    claim_status: Mapped[SupplierClaimStatus] = mapped_column(
        Enum(
            SupplierClaimStatus,
            name="procurement_supplier_claim_status",
        ),
        nullable=False,
        default=SupplierClaimStatus.NOT_REQUIRED,
    )

    supplier_return_authorization: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    authorized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    supplier_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )

    warehouse_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Warehouse service.",
    )

    shipment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Logistics/Fleet service.",
    )

    estimated_return_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

    supplier_claim_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    supplier_credit_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    finance_ap_adjustment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment=(
            "Reference to Finance/AP debit-credit adjustment "
            "created after return settlement."
        ),
    )

    finance_handoff_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    lines: Mapped[list["SupplierReturnLine"]] = relationship(
        back_populates="supplier_return",
        cascade="all, delete-orphan",
    )


class SupplierReturnLine(Base):
    __tablename__ = "procurement_supplier_return_lines"

    __table_args__ = (
        UniqueConstraint(
            "supplier_return_id",
            "line_number",
            name="uq_procurement_supplier_return_line_number",
        ),
        CheckConstraint(
            "return_quantity > 0",
            name="return_line_qty_pos",
        ),
        CheckConstraint(
            "unit_value >= 0",
            name="return_line_unit_nonneg",
        ),
        CheckConstraint(
            "line_value >= 0",
            name="return_line_value_nonneg",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    supplier_return_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_supplier_returns.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    goods_receipt_line_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_goods_receipt_lines.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    purchase_order_line_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "procurement_purchase_order_lines.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Inventory item master.",
    )

    lot_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    batch_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    return_quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    unit_of_measure: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    unit_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    line_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )

    reason: Mapped[SupplierReturnReason] = mapped_column(
        Enum(
            SupplierReturnReason,
            name="procurement_supplier_return_reason",
        ),
        nullable=False,
    )

    status: Mapped[SupplierReturnLineStatus] = mapped_column(
        Enum(
            SupplierReturnLineStatus,
            name="procurement_supplier_return_line_status",
        ),
        nullable=False,
        default=SupplierReturnLineStatus.PENDING,
    )

    inspection_reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    quality_case_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Reference to Quality/Laboratory service.",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    supplier_return: Mapped[SupplierReturn] = relationship(
        back_populates="lines",
    )
