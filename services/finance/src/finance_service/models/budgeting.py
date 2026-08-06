from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from finance_service.core.enums import (
    BudgetStatus,
    BudgetType,
    BudgetVersionStatus,
    CostAllocationMethod,
    CostObjectType,
    CostingMethod,
    PlanningScenario,
    VarianceType,
)
from finance_service.db.base import Base


class FinanceCostCentre(Base):
    __tablename__ = "finance_cost_centres"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_finance_cost_centre_tenant_code",
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
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    object_type: Mapped[CostObjectType] = mapped_column(
        Enum(CostObjectType, name="finance_cost_object_type"),
        nullable=False,
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_cost_centres.id"),
        nullable=True,
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    manager_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )


class FinanceProfitCentre(Base):
    __tablename__ = "finance_profit_centres"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_finance_profit_centre_tenant_code",
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
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    object_type: Mapped[CostObjectType] = mapped_column(
        Enum(CostObjectType, name="finance_profit_object_type"),
        nullable=False,
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_profit_centres.id"),
        nullable=True,
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    manager_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )


class FinanceBudget(Base):
    __tablename__ = "finance_budgets"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "budget_number",
            name="uq_finance_budget_tenant_number",
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
    budget_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    budget_type: Mapped[BudgetType] = mapped_column(
        Enum(BudgetType, name="finance_budget_type"),
        nullable=False,
    )
    fiscal_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fiscal_years.id"),
        nullable=False,
    )
    scenario: Mapped[PlanningScenario] = mapped_column(
        Enum(PlanningScenario, name="finance_planning_scenario"),
        nullable=False,
        default=PlanningScenario.BASE,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[BudgetStatus] = mapped_column(
        Enum(BudgetStatus, name="finance_budget_status"),
        nullable=False,
        default=BudgetStatus.DRAFT,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class FinanceBudgetVersion(Base):
    __tablename__ = "finance_budget_versions"
    __table_args__ = (
        UniqueConstraint(
            "budget_id",
            "version_number",
            name="uq_finance_budget_version_number",
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
    budget_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_budgets.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    version_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    status: Mapped[BudgetVersionStatus] = mapped_column(
        Enum(
            BudgetVersionStatus,
            name="finance_budget_version_status",
        ),
        nullable=False,
        default=BudgetVersionStatus.DRAFT,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
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


class FinanceBudgetLine(Base):
    __tablename__ = "finance_budget_lines"
    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "line_number",
            name="uq_finance_budget_line_version_number",
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
    version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_budget_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    ledger_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=False,
    )
    fiscal_period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fiscal_periods.id"),
        nullable=False,
    )
    cost_centre_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_cost_centres.id"),
        nullable=True,
    )
    profit_centre_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_profit_centres.id"),
        nullable=True,
    )
    object_type: Mapped[CostObjectType] = mapped_column(
        Enum(CostObjectType, name="finance_budget_object_type"),
        nullable=False,
    )
    object_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    unit_rate: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )


class FinanceCostAllocationRule(Base):
    __tablename__ = "finance_cost_allocation_rules"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "rule_code",
            name="uq_finance_allocation_rule_tenant_code",
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
    rule_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    allocation_method: Mapped[CostAllocationMethod] = mapped_column(
        Enum(
            CostAllocationMethod,
            name="finance_cost_allocation_method",
        ),
        nullable=False,
    )
    source_cost_centre_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_cost_centres.id"),
        nullable=False,
    )
    target_object_type: Mapped[CostObjectType] = mapped_column(
        Enum(
            CostObjectType,
            name="finance_allocation_target_object_type",
        ),
        nullable=False,
    )
    basis_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )


class FinanceStandardCost(Base):
    __tablename__ = "finance_standard_costs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "object_type",
            "object_reference",
            "effective_from",
            name="uq_finance_standard_cost_scope",
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
    object_type: Mapped[CostObjectType] = mapped_column(
        Enum(
            CostObjectType,
            name="finance_standard_cost_object_type",
        ),
        nullable=False,
    )
    object_reference: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    costing_method: Mapped[CostingMethod] = mapped_column(
        Enum(CostingMethod, name="finance_costing_method"),
        nullable=False,
    )
    material_cost: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    labour_cost: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    overhead_cost: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    total_standard_cost: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
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


class FinanceCostVariance(Base):
    __tablename__ = "finance_cost_variances"

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
    variance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    variance_type: Mapped[VarianceType] = mapped_column(
        Enum(VarianceType, name="finance_variance_type"),
        nullable=False,
    )
    object_type: Mapped[CostObjectType] = mapped_column(
        Enum(
            CostObjectType,
            name="finance_variance_object_type",
        ),
        nullable=False,
    )
    object_reference: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    budget_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    variance_percent: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
        default=Decimal("0"),
    )
    is_favourable: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
