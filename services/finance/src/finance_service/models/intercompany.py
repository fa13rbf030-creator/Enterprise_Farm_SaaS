from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Text,
    Numeric,
    Enum,
    Date,
    CheckConstraint,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from finance_service.db.base import Base



class IntercompanyRelationshipType(str, enum.Enum):
    PARENT_SUBSIDIARY = "parent_subsidiary"
    SISTER_COMPANY = "sister_company"
    JOINT_VENTURE = "joint_venture"
    ASSOCIATE = "associate"





class ConsolidationPeriodStatus(str, enum.Enum):
    OPEN = "open"
    DATA_COLLECTION = "data_collection"
    TRANSLATION = "translation"
    ELIMINATION = "elimination"
    REVIEW = "review"
    CLOSED = "closed"
    REOPENED = "reopened"


class TranslationRateType(str, enum.Enum):
    CLOSING = "closing"
    AVERAGE = "average"
    HISTORICAL = "historical"


class IntercompanyTransactionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHED = "matched"
    SETTLED = "settled"
    ELIMINATED = "eliminated"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class EliminationRuleType(str, enum.Enum):
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    INVESTMENT_EQUITY = "investment_equity"
    INTERCOMPANY_PROFIT = "intercompany_profit"
    DIVIDEND = "dividend"


class ConsolidationGroupStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class ConsolidationMemberMethod(str, enum.Enum):
    FULL = "full"
    PROPORTIONATE = "proportionate"
    EQUITY = "equity"


class IntercompanyOrganization(Base):
    __tablename__ = "finance_intercompany_organizations"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "organization_code",
            name="uq_ic_org_code",
        ),
        Index(
            "ix_ic_org_tenant",
            "tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    organization_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    organization_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    base_currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class IntercompanyRelationship(Base):
    __tablename__ = "finance_intercompany_relationships"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "parent_company_id",
            "child_company_id",
            name="uq_ic_relationship",
        ),
        Index(
            "ix_ic_relationship_tenant",
            "tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    parent_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_intercompany_organizations.id"
        ),
        nullable=False,
    )

    child_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_intercompany_organizations.id"
        ),
        nullable=False,
    )

    relationship_type: Mapped[IntercompanyRelationshipType] = mapped_column(
        Enum(
            IntercompanyRelationshipType,
            name="finance_intercompany_relationship_type",
        ),
        nullable=False,
        default=IntercompanyRelationshipType.PARENT_SUBSIDIARY,
    )

    ownership_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    voting_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )




class IntercompanyAccountMapping(Base):
    __tablename__ = "finance_intercompany_account_mappings"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_organization_id",
            "destination_organization_id",
            name="uq_ic_account_mapping_company_pair",
        ),
        CheckConstraint(
            "source_organization_id <> destination_organization_id",
            name="distinct_orgs",
        ),
        Index(
            "ix_ic_account_mapping_tenant",
            "tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    source_organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_intercompany_organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    destination_organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_intercompany_organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    source_due_from_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    source_due_to_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    destination_due_from_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    destination_due_to_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    settlement_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )


class ConsolidationGroup(Base):
    __tablename__ = "finance_consolidation_groups"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "group_code",
            name="uq_finance_consolidation_group_tenant_code",
        ),
        Index(
            "ix_finance_consolidation_group_tenant",
            "tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    group_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    group_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    parent_organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_intercompany_organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    presentation_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    status: Mapped[ConsolidationGroupStatus] = mapped_column(
        Enum(
            ConsolidationGroupStatus,
            name="finance_consolidation_group_status",
        ),
        nullable=False,
        default=ConsolidationGroupStatus.DRAFT,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class ConsolidationGroupMember(Base):
    __tablename__ = "finance_consolidation_group_members"

    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "organization_id",
            name="uq_finance_consolidation_group_member",
        ),
        CheckConstraint(
            "ownership_percentage >= 0 AND ownership_percentage <= 100",
            name="ownership_pct",
        ),
        CheckConstraint(
            "voting_percentage >= 0 AND voting_percentage <= 100",
            name="voting_pct",
        ),
        Index(
            "ix_finance_consolidation_member_tenant",
            "tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_consolidation_groups.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_intercompany_organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    consolidation_method: Mapped[ConsolidationMemberMethod] = mapped_column(
        Enum(
            ConsolidationMemberMethod,
            name="finance_consolidation_member_method",
        ),
        nullable=False,
        default=ConsolidationMemberMethod.FULL,
    )
    ownership_percentage: Mapped[Decimal] = mapped_column(
        Numeric(7, 4),
        nullable=False,
        default=Decimal("100"),
    )
    voting_percentage: Mapped[Decimal] = mapped_column(
        Numeric(7, 4),
        nullable=False,
        default=Decimal("100"),
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )



class ConsolidationPeriod(Base):
    __tablename__ = "finance_consolidation_periods"

    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "period_start",
            "period_end",
            name="uq_finance_consolidation_period_range",
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="valid_range",
        ),
        Index(
            "ix_finance_consolidation_period_tenant",
            "tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_consolidation_groups.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    period_name: Mapped[str] = mapped_column(
        String(100),
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
    status: Mapped[ConsolidationPeriodStatus] = mapped_column(
        Enum(
            ConsolidationPeriodStatus,
            name="finance_consolidation_period_status",
        ),
        nullable=False,
        default=ConsolidationPeriodStatus.OPEN,
    )
    presentation_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    opened_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    closed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )


class CurrencyTranslationRule(Base):
    __tablename__ = "finance_currency_translation_rules"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "group_id",
            "account_type",
            name="uq_finance_translation_rule_scope",
        ),
        Index(
            "ix_finance_translation_rule_tenant",
            "tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_consolidation_groups.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    account_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    rate_type: Mapped[TranslationRateType] = mapped_column(
        Enum(
            TranslationRateType,
            name="finance_translation_rate_type",
        ),
        nullable=False,
    )
    translation_adjustment_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class EliminationRule(Base):
    __tablename__ = "finance_elimination_rules"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "group_id",
            "rule_code",
            name="uq_finance_elimination_rule_code",
        ),
        Index(
            "ix_finance_elimination_rule_tenant",
            "tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_consolidation_groups.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    rule_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    rule_type: Mapped[EliminationRuleType] = mapped_column(
        Enum(
            EliminationRuleType,
            name="finance_elimination_rule_type",
        ),
        nullable=False,
    )
    source_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    counterparty_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    elimination_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class IntercompanyTransaction(Base):
    __tablename__ = "finance_intercompany_transactions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "transaction_number",
            name="uq_finance_intercompany_transaction_number",
        ),
        CheckConstraint(
            "source_organization_id <> destination_organization_id",
            name="distinct_orgs",
        ),
        CheckConstraint(
            "amount > 0",
            name="positive_amount",
        ),
        Index(
            "ix_finance_intercompany_transaction_tenant",
            "tenant_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    transaction_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    source_organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_intercompany_organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    destination_organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_intercompany_organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(24, 10),
        nullable=False,
        default=Decimal("1"),
    )
    base_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    source_journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("finance_journal_entries.id"),
        nullable=True,
    )
    destination_journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("finance_journal_entries.id"),
        nullable=True,
    )
    source_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    destination_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    status: Mapped[IntercompanyTransactionStatus] = mapped_column(
        Enum(
            IntercompanyTransactionStatus,
            name="finance_intercompany_transaction_status",
        ),
        nullable=False,
        default=IntercompanyTransactionStatus.DRAFT,
    )
    elimination_period_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "finance_consolidation_periods.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
