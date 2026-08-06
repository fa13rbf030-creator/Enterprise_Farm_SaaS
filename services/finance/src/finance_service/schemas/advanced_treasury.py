from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from finance_service.core.enums import (
    CashPoolStatus,
    CashPoolType,
    DebtInstrumentType,
    DebtStatus,
    FxExposureStatus,
    FxExposureType,
    HedgeInstrumentType,
    HedgeStatus,
    InvestmentStatus,
    InvestmentType,
    StressScenarioType,
    TradeFinanceInstrumentType,
    TradeFinanceStatus,
    TreasuryTransferStatus,
)


class CashPoolMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bank_account_id: UUID
    minimum_balance: Decimal = Field(default=Decimal("0"), ge=0)
    target_balance: Decimal = Field(default=Decimal("0"), ge=0)
    priority: int = Field(default=1, ge=1)


class CashPoolCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    pool_code: str = Field(min_length=1, max_length=50)
    pool_name: str = Field(min_length=1, max_length=200)
    pool_type: CashPoolType
    header_bank_account_id: UUID
    currency_code: str = Field(min_length=3, max_length=3)
    target_balance: Decimal = Field(default=Decimal("0"), ge=0)
    created_by: UUID
    members: list[CashPoolMemberCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_members(self):
        account_ids = [member.bank_account_id for member in self.members]

        if len(account_ids) != len(set(account_ids)):
            raise ValueError("Cash-pool member accounts must be unique")

        if self.header_bank_account_id in account_ids:
            raise ValueError(
                "Header bank account cannot also be a member account"
            )

        return self


class CashPoolMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pool_id: UUID
    bank_account_id: UUID
    minimum_balance: Decimal
    target_balance: Decimal
    priority: int


class CashPoolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    pool_code: str
    pool_name: str
    pool_type: CashPoolType
    header_bank_account_id: UUID
    currency_code: str
    target_balance: Decimal
    status: CashPoolStatus
    created_by: UUID


class CashPoolDetailRead(CashPoolRead):
    members: list[CashPoolMemberRead]


class CashPoolActivateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    activated_by: UUID


class CashPoolSweepLineRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bank_account_id: UUID
    current_balance: Decimal
    retained_balance: Decimal
    sweep_amount: Decimal


class CashPoolSweepRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pool_id: UUID
    currency_code: str
    total_sweep_amount: Decimal
    header_balance_before: Decimal
    header_balance_after: Decimal
    lines: list[CashPoolSweepLineRead]


class IntercompanyTransferCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    transfer_number: str = Field(min_length=1, max_length=100)
    transfer_date: date
    source_bank_account_id: UUID
    destination_bank_account_id: UUID
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)
    created_by: UUID
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def validate_accounts(self):
        if self.source_bank_account_id == self.destination_bank_account_id:
            raise ValueError(
                "Source and destination bank accounts must differ"
            )

        return self


class IntercompanyTransferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    transfer_number: str
    transfer_date: date
    source_bank_account_id: UUID
    destination_bank_account_id: UUID
    amount: Decimal
    currency_code: str
    exchange_rate: Decimal
    destination_amount: Decimal
    status: TreasuryTransferStatus
    created_by: UUID
    approved_by: UUID | None
    journal_entry_id: UUID | None


class TransferApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    approved_by: UUID


class FxExposureCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    exposure_number: str = Field(min_length=1, max_length=100)
    exposure_type: FxExposureType
    source_reference: str | None = Field(default=None, max_length=200)
    exposure_date: date
    maturity_date: date
    foreign_currency: str = Field(min_length=3, max_length=3)
    base_currency: str = Field(min_length=3, max_length=3)
    foreign_amount: Decimal = Field(gt=0)
    spot_rate: Decimal = Field(gt=0)
    created_by: UUID

    @model_validator(mode="after")
    def validate_exposure(self):
        if self.maturity_date < self.exposure_date:
            raise ValueError(
                "Exposure maturity cannot precede exposure date"
            )

        if self.foreign_currency.upper() == self.base_currency.upper():
            raise ValueError(
                "Foreign and base currencies must differ"
            )

        return self


class FxExposureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    exposure_number: str
    exposure_type: FxExposureType
    exposure_date: date
    maturity_date: date
    foreign_currency: str
    base_currency: str
    foreign_amount: Decimal
    spot_rate: Decimal
    base_amount: Decimal
    hedged_amount: Decimal
    unhedged_amount: Decimal
    status: FxExposureStatus


class HedgeContractCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    exposure_id: UUID
    contract_number: str = Field(min_length=1, max_length=100)
    instrument_type: HedgeInstrumentType
    counterparty: str = Field(min_length=1, max_length=200)
    trade_date: date
    maturity_date: date
    hedge_amount: Decimal = Field(gt=0)
    contracted_rate: Decimal = Field(gt=0)
    created_by: UUID

    @model_validator(mode="after")
    def validate_dates(self):
        if self.maturity_date < self.trade_date:
            raise ValueError(
                "Hedge maturity cannot precede trade date"
            )

        return self


class HedgeContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    exposure_id: UUID
    contract_number: str
    instrument_type: HedgeInstrumentType
    counterparty: str
    trade_date: date
    maturity_date: date
    hedge_amount: Decimal
    contracted_rate: Decimal
    status: HedgeStatus
    created_by: UUID
    approved_by: UUID | None


class HedgeApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    approved_by: UUID


class DebtInstrumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    instrument_number: str = Field(min_length=1, max_length=100)
    instrument_type: DebtInstrumentType
    lender_name: str = Field(min_length=1, max_length=200)
    currency_code: str = Field(min_length=3, max_length=3)
    principal_amount: Decimal = Field(gt=0)
    annual_rate: Decimal = Field(ge=0)
    start_date: date
    maturity_date: date
    created_by: UUID

    @model_validator(mode="after")
    def validate_dates(self):
        if self.maturity_date <= self.start_date:
            raise ValueError(
                "Debt maturity must follow start date"
            )

        return self


class DebtInstrumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    instrument_number: str
    instrument_type: DebtInstrumentType
    lender_name: str
    currency_code: str
    principal_amount: Decimal
    outstanding_principal: Decimal
    annual_rate: Decimal
    start_date: date
    maturity_date: date
    status: DebtStatus


class TradeFinanceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    instrument_number: str = Field(min_length=1, max_length=100)
    instrument_type: TradeFinanceInstrumentType
    issuing_bank: str = Field(min_length=1, max_length=200)
    beneficiary_name: str = Field(min_length=1, max_length=200)
    currency_code: str = Field(min_length=3, max_length=3)
    amount: Decimal = Field(gt=0)
    issue_date: date | None = None
    expiry_date: date
    created_by: UUID


class TradeFinanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    instrument_number: str
    instrument_type: TradeFinanceInstrumentType
    issuing_bank: str
    beneficiary_name: str
    currency_code: str
    amount: Decimal
    utilized_amount: Decimal
    issue_date: date | None
    expiry_date: date
    status: TradeFinanceStatus


class InvestmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    investment_number: str = Field(min_length=1, max_length=100)
    investment_type: InvestmentType
    institution_name: str = Field(min_length=1, max_length=200)
    currency_code: str = Field(min_length=3, max_length=3)
    principal_amount: Decimal = Field(gt=0)
    expected_return_rate: Decimal = Field(ge=0)
    investment_date: date
    maturity_date: date
    created_by: UUID

    @model_validator(mode="after")
    def validate_dates(self):
        if self.maturity_date <= self.investment_date:
            raise ValueError(
                "Investment maturity must follow investment date"
            )

        return self


class InvestmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    investment_number: str
    investment_type: InvestmentType
    institution_name: str
    currency_code: str
    principal_amount: Decimal
    expected_return_rate: Decimal
    investment_date: date
    maturity_date: date
    expected_maturity_value: Decimal
    status: InvestmentStatus


class StressTestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    test_date: date
    scenario_type: StressScenarioType
    scenario_name: str = Field(min_length=1, max_length=200)
    opening_liquidity: Decimal
    expected_inflows: Decimal = Field(ge=0)
    expected_outflows: Decimal = Field(ge=0)
    inflow_reduction_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    outflow_increase_percent: Decimal = Field(default=Decimal("0"), ge=0)
    fx_shock_percent: Decimal = Field(default=Decimal("0"), ge=0)
    minimum_buffer: Decimal = Field(default=Decimal("0"), ge=0)
    created_by: UUID


class StressTestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    test_date: date
    scenario_type: StressScenarioType
    scenario_name: str
    opening_liquidity: Decimal
    inflow_reduction_percent: Decimal
    outflow_increase_percent: Decimal
    fx_shock_percent: Decimal
    stressed_liquidity: Decimal
    liquidity_shortfall: Decimal


class AdvancedTreasuryDashboardRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    active_cash_pools: int
    pending_transfers: int
    open_fx_exposures: int
    total_unhedged_foreign_amount: Decimal
    active_debt_principal: Decimal
    outstanding_trade_finance: Decimal
    active_investments: Decimal
    latest_stress_shortfall: Decimal
