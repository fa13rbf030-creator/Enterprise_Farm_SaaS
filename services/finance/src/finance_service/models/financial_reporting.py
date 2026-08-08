from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from finance_service.core.enums import (
    FinancialReportBasis,
    FinancialReportLineType,
    FinancialReportPeriodType,
    FinancialReportPresentation,
    FinancialReportStandard,
    FinancialReportStatus,
    FinancialReportType,
)
from finance_service.db.base import Base


class FinancialReportDefinition(Base):
    __tablename__ = "finance_report_definitions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "report_code",
            name="uq_finance_report_definition_tenant_code",
        ),
        Index(
            "ix_finance_report_definition_tenant",
            "tenant_id",
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
    report_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    report_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    report_type: Mapped[FinancialReportType] = mapped_column(
        Enum(
            FinancialReportType,
            name="finance_report_type",
        ),
        nullable=False,
    )
    reporting_standard: Mapped[FinancialReportStandard] = mapped_column(
        Enum(
            FinancialReportStandard,
            name="finance_report_standard",
        ),
        nullable=False,
        default=FinancialReportStandard.IFRS,
    )
    accounting_basis: Mapped[FinancialReportBasis] = mapped_column(
        Enum(
            FinancialReportBasis,
            name="finance_report_basis",
        ),
        nullable=False,
        default=FinancialReportBasis.ACCRUAL,
    )
    default_presentation: Mapped[FinancialReportPresentation] = mapped_column(
        Enum(
            FinancialReportPresentation,
            name="finance_report_presentation",
        ),
        nullable=False,
        default=FinancialReportPresentation.SINGLE_PERIOD,
    )
    presentation_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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


class FinancialReportLayout(Base):
    __tablename__ = "finance_report_layouts"

    __table_args__ = (
        UniqueConstraint(
            "definition_id",
            "layout_code",
            name="uq_finance_report_layout_definition_code",
        ),
        Index(
            "ix_finance_report_layout_tenant",
            "tenant_id",
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
    )
    definition_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_report_definitions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    layout_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    layout_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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


class FinancialReportLayoutLine(Base):
    __tablename__ = "finance_report_layout_lines"

    __table_args__ = (
        UniqueConstraint(
            "layout_id",
            "line_code",
            name="uq_finance_report_layout_line_code",
        ),
        CheckConstraint(
            "display_order >= 0",
            name="display_order",
        ),
        Index(
            "ix_finance_report_layout_line_tenant",
            "tenant_id",
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
    )
    layout_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_report_layouts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    parent_line_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_report_layout_lines.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    line_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    line_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    line_type: Mapped[FinancialReportLineType] = mapped_column(
        Enum(
            FinancialReportLineType,
            name="finance_report_line_type",
        ),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    account_filter: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    formula_expression: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    style_configuration: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class FinancialReportRun(Base):
    __tablename__ = "finance_report_runs"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "run_number",
            name="uq_finance_report_run_number",
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_finance_report_run_valid_period",
        ),
        Index(
            "ix_finance_report_run_tenant_status",
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
    )
    definition_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_report_definitions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    layout_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_report_layouts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    run_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    period_type: Mapped[FinancialReportPeriodType] = mapped_column(
        Enum(
            FinancialReportPeriodType,
            name="finance_report_period_type",
        ),
        nullable=False,
    )
    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    comparative_period_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    comparative_period_end: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    presentation: Mapped[FinancialReportPresentation] = mapped_column(
        Enum(
            FinancialReportPresentation,
            name="finance_report_run_presentation",
        ),
        nullable=False,
    )
    presentation_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    consolidation_group_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_consolidation_groups.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    budget_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_budgets.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    segment_filter: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    status: Mapped[FinancialReportStatus] = mapped_column(
        Enum(
            FinancialReportStatus,
            name="finance_report_status",
        ),
        nullable=False,
        default=FinancialReportStatus.DRAFT,
    )
    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    parameters: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class FinancialReportSnapshot(Base):
    __tablename__ = "finance_report_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "snapshot_number",
            name="uq_finance_report_snapshot_number",
        ),
        Index(
            "ix_finance_report_snapshot_tenant",
            "tenant_id",
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
    )
    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_report_runs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    snapshot_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    snapshot_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
    document_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    generated_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    is_final: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


class FinancialDisclosureDefinition(Base):
    __tablename__ = "finance_disclosure_definitions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "disclosure_code",
            name="uq_finance_disclosure_definition_code",
        ),
        Index(
            "ix_finance_disclosure_definition_tenant",
            "tenant_id",
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
    )
    disclosure_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    disclosure_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    reporting_standard: Mapped[FinancialReportStandard] = mapped_column(
        Enum(
            FinancialReportStandard,
            name="finance_disclosure_standard",
        ),
        nullable=False,
    )
    standard_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    data_requirements: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
