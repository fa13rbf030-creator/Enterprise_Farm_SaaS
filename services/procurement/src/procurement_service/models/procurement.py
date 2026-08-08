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
    RequisitionPriority,
    RequisitionStatus,
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
