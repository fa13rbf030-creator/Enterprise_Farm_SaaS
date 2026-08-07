from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from finance_service.db.base import Base


class IslamicRuleStatus(str, __import__("enum").Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    RETIRED = "retired"


class IslamicAssessmentType(str, __import__("enum").Enum):
    MONETARY_ZAKAT = "monetary_zakat"
    LIVESTOCK_ZAKAT = "livestock_zakat"
    CROP_USHR = "crop_ushr"
    SADAQAH = "sadaqah"


class IslamicAssessmentStatus(str, __import__("enum").Enum):
    DRAFT = "draft"
    CALCULATED = "calculated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class ShariahRuleSet(Base):
    __tablename__ = "finance_shariah_rule_sets"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "rule_code",
            "version_number",
            name="uq_finance_shariah_rule_version",
        ),
        Index(
            "ix_finance_shariah_rule_tenant",
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
    rule_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    status: Mapped[IslamicRuleStatus] = mapped_column(
        Enum(
            IslamicRuleStatus,
            name="finance_islamic_rule_status",
        ),
        nullable=False,
        default=IslamicRuleStatus.DRAFT,
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    shariah_reference: Mapped[str | None] = mapped_column(
        String(500),
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
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )


class NisabReference(Base):
    __tablename__ = "finance_nisab_references"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "rule_set_id",
            "reference_date",
            name="uq_finance_nisab_reference_date",
        ),
        Index(
            "ix_finance_nisab_reference_tenant",
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
    rule_set_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_shariah_rule_sets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    reference_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    reference_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    nisab_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )


class ZakatAssessment(Base):
    __tablename__ = "finance_zakat_assessments"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "assessment_number",
            name="uq_finance_zakat_assessment_number",
        ),
        Index(
            "ix_finance_zakat_assessment_tenant_status",
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
    rule_set_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_shariah_rule_sets.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    nisab_reference_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_nisab_references.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    assessment_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    assessment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    eligible_assets: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    deductible_liabilities: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    zakatable_base: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    nisab_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    rate_percentage: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
        default=Decimal("0"),
    )
    holding_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    required_hawl_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=354,
    )
    zakat_due: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[IslamicAssessmentStatus] = mapped_column(
        Enum(
            IslamicAssessmentStatus,
            name="finance_islamic_assessment_status",
        ),
        nullable=False,
        default=IslamicAssessmentStatus.DRAFT,
    )
    prepared_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class UshrAssessment(Base):
    __tablename__ = "finance_ushr_assessments"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "assessment_number",
            name="uq_finance_ushr_assessment_number",
        ),
        CheckConstraint(
            "rate_percentage >= 0 AND rate_percentage <= 100",
            name="ck_finance_ushr_rate",
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
    rule_set_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_shariah_rule_sets.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    assessment_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    crop_batch_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    harvest_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    irrigation_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    eligible_output_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    rate_percentage: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
    )
    ushr_due: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[IslamicAssessmentStatus] = mapped_column(
        Enum(
            IslamicAssessmentStatus,
            name="finance_ushr_assessment_status",
        ),
        nullable=False,
        default=IslamicAssessmentStatus.DRAFT,
    )
    prepared_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )


class LivestockZakatRule(Base):
    __tablename__ = "finance_livestock_zakat_rules"

    __table_args__ = (
        UniqueConstraint(
            "rule_set_id",
            "species_code",
            "minimum_count",
            name="uq_finance_livestock_zakat_rule",
        ),
        CheckConstraint(
            "maximum_count IS NULL OR maximum_count >= minimum_count",
            name="ck_finance_livestock_zakat_count_range",
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
    rule_set_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_shariah_rule_sets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    species_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    minimum_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    maximum_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    obligation_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    obligation_unit: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )


class SadaqahTransaction(Base):
    __tablename__ = "finance_sadaqah_transactions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "transaction_number",
            name="uq_finance_sadaqah_transaction_number",
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
    transaction_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    beneficiary_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    purpose: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    recorded_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )


class IslamicDisbursementEvidence(Base):
    __tablename__ = "finance_islamic_disbursement_evidence"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "evidence_number",
            name="uq_finance_islamic_disbursement_evidence",
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
    assessment_type: Mapped[IslamicAssessmentType] = mapped_column(
        Enum(
            IslamicAssessmentType,
            name="finance_islamic_assessment_type",
        ),
        nullable=False,
    )
    assessment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    evidence_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    disbursement_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    beneficiary_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    document_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
