from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

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


class CostCentreCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    object_type: CostObjectType
    parent_id: UUID | None = None
    external_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    manager_id: UUID | None = None
    description: str = Field(default="", max_length=2000)


class CostCentreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    object_type: CostObjectType
    parent_id: UUID | None
    external_reference: str | None
    manager_id: UUID | None
    is_active: bool
    description: str


class ProfitCentreCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    object_type: CostObjectType
    parent_id: UUID | None = None
    external_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    manager_id: UUID | None = None


class ProfitCentreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    object_type: CostObjectType
    parent_id: UUID | None
    external_reference: str | None
    manager_id: UUID | None
    is_active: bool


class BudgetLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_number: int = Field(ge=1)
    ledger_account_id: UUID
    fiscal_period_id: UUID
    cost_centre_id: UUID | None = None
    profit_centre_id: UUID | None = None
    object_type: CostObjectType
    object_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    quantity: Decimal = Field(default=Decimal("0"), ge=0)
    unit_rate: Decimal = Field(default=Decimal("0"), ge=0)
    amount: Decimal | None = Field(default=None, ge=0)
    description: str = Field(default="", max_length=500)


class BudgetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    budget_number: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    budget_type: BudgetType
    fiscal_year_id: UUID
    scenario: PlanningScenario = PlanningScenario.BASE
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    starts_on: date
    ends_on: date
    created_by: UUID
    notes: str = Field(default="", max_length=2000)
    version_name: str = Field(
        default="Initial Version",
        min_length=1,
        max_length=200,
    )
    lines: list[BudgetLineCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_budget(self):
        if self.ends_on < self.starts_on:
            raise ValueError(
                "Budget end date cannot precede start date"
            )

        line_numbers = [
            line.line_number
            for line in self.lines
        ]

        if len(line_numbers) != len(set(line_numbers)):
            raise ValueError(
                "Budget line numbers must be unique"
            )

        return self


class BudgetLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    version_id: UUID
    line_number: int
    ledger_account_id: UUID
    fiscal_period_id: UUID
    cost_centre_id: UUID | None
    profit_centre_id: UUID | None
    object_type: CostObjectType
    object_reference: str | None
    quantity: Decimal
    unit_rate: Decimal
    amount: Decimal
    description: str


class BudgetVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    budget_id: UUID
    version_number: int
    version_name: str
    status: BudgetVersionStatus
    total_amount: Decimal
    created_by: UUID


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    budget_number: str
    name: str
    budget_type: BudgetType
    fiscal_year_id: UUID
    scenario: PlanningScenario
    currency_code: str
    starts_on: date
    ends_on: date
    total_amount: Decimal
    status: BudgetStatus
    created_by: UUID
    approved_by: UUID | None
    notes: str


class BudgetDetailRead(BudgetRead):
    version: BudgetVersionRead
    lines: list[BudgetLineRead]


class BudgetSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    submitted_by: UUID


class BudgetApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    approved_by: UUID
    approve: bool = True


class StandardCostCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    object_type: CostObjectType
    object_reference: str = Field(
        min_length=1,
        max_length=200,
    )
    costing_method: CostingMethod
    material_cost: Decimal = Field(default=Decimal("0"), ge=0)
    labour_cost: Decimal = Field(default=Decimal("0"), ge=0)
    overhead_cost: Decimal = Field(default=Decimal("0"), ge=0)
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "Effective-to date cannot precede effective-from"
            )

        return self


class StandardCostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    object_type: CostObjectType
    object_reference: str
    costing_method: CostingMethod
    material_cost: Decimal
    labour_cost: Decimal
    overhead_cost: Decimal
    total_standard_cost: Decimal
    effective_from: date
    effective_to: date | None


class CostVarianceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    variance_date: date
    variance_type: VarianceType
    object_type: CostObjectType
    object_reference: str = Field(
        min_length=1,
        max_length=200,
    )
    budget_amount: Decimal
    actual_amount: Decimal
    expense_nature: bool = True


class CostVarianceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    variance_date: date
    variance_type: VarianceType
    object_type: CostObjectType
    object_reference: str
    budget_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percent: Decimal
    is_favourable: bool


class CostAllocationRuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    rule_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    allocation_method: CostAllocationMethod
    source_cost_centre_id: UUID
    target_object_type: CostObjectType
    basis_reference: str | None = Field(
        default=None,
        max_length=200,
    )


class CostAllocationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rule_code: str
    name: str
    allocation_method: CostAllocationMethod
    source_cost_centre_id: UUID
    target_object_type: CostObjectType
    basis_reference: str | None
    is_active: bool
