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
from finance_service.db.base import Base


class TreasuryCashPool(Base):
    __tablename__ = "finance_treasury_cash_pools"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "pool_code",
            name="uq_finance_cash_pool_tenant_code",
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
    pool_code: Mapped[str] = mapped_column(String(50), nullable=False)
    pool_name: Mapped[str] = mapped_column(String(200), nullable=False)
    pool_type: Mapped[CashPoolType] = mapped_column(
        Enum(CashPoolType, name="finance_cash_pool_type"),
        nullable=False,
    )
    header_bank_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_bank_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    target_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[CashPoolStatus] = mapped_column(
        Enum(CashPoolStatus, name="finance_cash_pool_status"),
        nullable=False,
        default=CashPoolStatus.DRAFT,
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


class TreasuryCashPoolMember(Base):
    __tablename__ = "finance_treasury_cash_pool_members"
    __table_args__ = (
        UniqueConstraint(
            "pool_id",
            "bank_account_id",
            name="uq_finance_cash_pool_member_account",
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
    pool_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_treasury_cash_pools.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    bank_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_bank_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    minimum_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    target_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    priority: Mapped[int] = mapped_column(nullable=False, default=1)


class TreasuryIntercompanyTransfer(Base):
    __tablename__ = "finance_treasury_intercompany_transfers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "transfer_number",
            name="uq_finance_treasury_transfer_tenant_number",
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
    transfer_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_bank_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_bank_accounts.id"),
        nullable=False,
    )
    destination_bank_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_bank_accounts.id"),
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
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(24, 10),
        nullable=False,
        default=Decimal("1"),
    )
    destination_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    status: Mapped[TreasuryTransferStatus] = mapped_column(
        Enum(
            TreasuryTransferStatus,
            name="finance_treasury_transfer_status",
        ),
        nullable=False,
        default=TreasuryTransferStatus.DRAFT,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
    )
    journal_entry_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_journal_entries.id"),
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


class TreasuryFxExposure(Base):
    __tablename__ = "finance_treasury_fx_exposures"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "exposure_number",
            name="uq_finance_fx_exposure_tenant_number",
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
    exposure_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    exposure_type: Mapped[FxExposureType] = mapped_column(
        Enum(FxExposureType, name="finance_fx_exposure_type"),
        nullable=False,
    )
    source_reference: Mapped[str | None] = mapped_column(
        String(200),
    )
    exposure_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    foreign_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    base_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    foreign_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    spot_rate: Mapped[Decimal] = mapped_column(
        Numeric(24, 10),
        nullable=False,
    )
    base_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    hedged_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    unhedged_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    status: Mapped[FxExposureStatus] = mapped_column(
        Enum(FxExposureStatus, name="finance_fx_exposure_status"),
        nullable=False,
        default=FxExposureStatus.OPEN,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )


class TreasuryHedgeContract(Base):
    __tablename__ = "finance_treasury_hedge_contracts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "contract_number",
            name="uq_finance_hedge_contract_tenant_number",
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
    exposure_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_treasury_fx_exposures.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    contract_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    instrument_type: Mapped[HedgeInstrumentType] = mapped_column(
        Enum(
            HedgeInstrumentType,
            name="finance_hedge_instrument_type",
        ),
        nullable=False,
    )
    counterparty: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    hedge_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    contracted_rate: Mapped[Decimal] = mapped_column(
        Numeric(24, 10),
        nullable=False,
    )
    status: Mapped[HedgeStatus] = mapped_column(
        Enum(HedgeStatus, name="finance_hedge_status"),
        nullable=False,
        default=HedgeStatus.PROPOSED,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
    )


class TreasuryDebtInstrument(Base):
    __tablename__ = "finance_treasury_debt_instruments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "instrument_number",
            name="uq_finance_debt_instrument_tenant_number",
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
    instrument_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    instrument_type: Mapped[DebtInstrumentType] = mapped_column(
        Enum(
            DebtInstrumentType,
            name="finance_debt_instrument_type",
        ),
        nullable=False,
    )
    lender_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    outstanding_principal: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    annual_rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DebtStatus] = mapped_column(
        Enum(DebtStatus, name="finance_debt_status"),
        nullable=False,
        default=DebtStatus.DRAFT,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )


class TreasuryTradeFinanceInstrument(Base):
    __tablename__ = "finance_treasury_trade_finance"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "instrument_number",
            name="uq_finance_trade_finance_tenant_number",
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
    instrument_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    instrument_type: Mapped[TradeFinanceInstrumentType] = mapped_column(
        Enum(
            TradeFinanceInstrumentType,
            name="finance_trade_finance_type",
        ),
        nullable=False,
    )
    issuing_bank: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    beneficiary_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    utilized_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TradeFinanceStatus] = mapped_column(
        Enum(
            TradeFinanceStatus,
            name="finance_trade_finance_status",
        ),
        nullable=False,
        default=TradeFinanceStatus.DRAFT,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )


class TreasuryInvestment(Base):
    __tablename__ = "finance_treasury_investments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "investment_number",
            name="uq_finance_investment_tenant_number",
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
    investment_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    investment_type: Mapped[InvestmentType] = mapped_column(
        Enum(InvestmentType, name="finance_investment_type"),
        nullable=False,
    )
    institution_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    expected_return_rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        nullable=False,
    )
    investment_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_maturity_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    status: Mapped[InvestmentStatus] = mapped_column(
        Enum(InvestmentStatus, name="finance_investment_status"),
        nullable=False,
        default=InvestmentStatus.PROPOSED,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )


class TreasuryStressTest(Base):
    __tablename__ = "finance_treasury_stress_tests"

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
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    scenario_type: Mapped[StressScenarioType] = mapped_column(
        Enum(
            StressScenarioType,
            name="finance_stress_scenario_type",
        ),
        nullable=False,
    )
    scenario_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    opening_liquidity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    inflow_reduction_percent: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        nullable=False,
        default=Decimal("0"),
    )
    outflow_increase_percent: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        nullable=False,
        default=Decimal("0"),
    )
    fx_shock_percent: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        nullable=False,
        default=Decimal("0"),
    )
    stressed_liquidity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    liquidity_shortfall: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
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
