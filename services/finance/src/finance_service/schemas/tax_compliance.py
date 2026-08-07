from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from finance_service.models.tax_compliance import (
    StatutoryFilingStatus,
    TaxReturnStatus,
    TaxType,
)


class TaxJurisdictionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    jurisdiction_code: str = Field(min_length=1, max_length=100)
    jurisdiction_name: str = Field(min_length=1, max_length=255)
    country_code: str = Field(min_length=2, max_length=3)
    region_code: str | None = Field(default=None, max_length=50)
    authority_name: str = Field(min_length=1, max_length=255)
    authority_reference: str | None = Field(
        default=None,
        max_length=255,
    )


class TaxJurisdictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    jurisdiction_code: str
    jurisdiction_name: str
    country_code: str
    region_code: str | None
    authority_name: str
    authority_reference: str | None
    is_active: bool


class TaxRegistrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    jurisdiction_id: UUID
    registration_number: str = Field(min_length=1, max_length=150)
    legal_name: str = Field(min_length=1, max_length=255)
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "Registration end cannot precede start"
            )
        return self


class TaxRegistrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    jurisdiction_id: UUID
    registration_number: str
    legal_name: str
    effective_from: date
    effective_to: date | None
    is_active: bool


class TaxCodeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    jurisdiction_id: UUID
    tax_code: str = Field(min_length=1, max_length=100)
    tax_name: str = Field(min_length=1, max_length=255)
    tax_type: TaxType
    input_tax_account_id: UUID | None = None
    output_tax_account_id: UUID | None = None
    payable_account_id: UUID | None = None
    recoverable_account_id: UUID | None = None
    is_recoverable: bool = True


class TaxCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    jurisdiction_id: UUID
    tax_code: str
    tax_name: str
    tax_type: TaxType
    input_tax_account_id: UUID | None
    output_tax_account_id: UUID | None
    payable_account_id: UUID | None
    recoverable_account_id: UUID | None
    is_recoverable: bool
    is_active: bool


class TaxRateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    tax_code_id: UUID
    rate: Decimal = Field(ge=0, le=100)
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "Tax rate end cannot precede start"
            )
        return self


class TaxRateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    tax_code_id: UUID
    rate: Decimal
    effective_from: date
    effective_to: date | None


class WithholdingTaxRuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    jurisdiction_id: UUID
    rule_code: str = Field(min_length=1, max_length=100)
    rule_name: str = Field(min_length=1, max_length=255)
    rate: Decimal = Field(ge=0, le=100)
    threshold_amount: Decimal = Field(default=Decimal("0"), ge=0)
    effective_from: date
    effective_to: date | None = None


class TaxPeriodCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    registration_id: UUID
    period_name: str = Field(min_length=1, max_length=100)
    period_start: date
    period_end: date
    filing_due_date: date
    payment_due_date: date | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError(
                "Tax period end cannot precede start"
            )
        if self.filing_due_date < self.period_end:
            raise ValueError(
                "Filing due date cannot precede period end"
            )
        return self


class TaxPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    registration_id: UUID
    period_name: str
    period_start: date
    period_end: date
    filing_due_date: date
    payment_due_date: date | None
    is_closed: bool


class TaxReturnCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    tax_period_id: UUID
    return_number: str = Field(min_length=1, max_length=100)
    output_tax: Decimal = Field(default=Decimal("0"), ge=0)
    input_tax: Decimal = Field(default=Decimal("0"), ge=0)
    withholding_tax: Decimal = Field(default=Decimal("0"), ge=0)
    adjustments: Decimal = Decimal("0")
    credits: Decimal = Field(default=Decimal("0"), ge=0)
    prepared_by: UUID


class TaxReturnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    tax_period_id: UUID
    return_number: str
    status: TaxReturnStatus
    output_tax: Decimal
    input_tax: Decimal
    withholding_tax: Decimal
    adjustments: Decimal
    credits: Decimal
    net_tax_liability: Decimal
    prepared_by: UUID
    filed_by: UUID | None
    filed_at: datetime | None
    authority_reference: str | None


class StatutoryFilingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    tax_return_id: UUID | None = None
    filing_number: str = Field(min_length=1, max_length=100)
    filing_type: str = Field(min_length=1, max_length=100)
    due_date: date
    document_reference: str | None = Field(
        default=None,
        max_length=500,
    )
    notes: str = Field(default="", max_length=4000)


class StatutoryFilingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    tax_return_id: UUID | None
    filing_number: str
    filing_type: str
    due_date: date
    status: StatutoryFilingStatus
    document_reference: str | None
    submission_reference: str | None
    submitted_by: UUID | None
    submitted_at: datetime | None
    notes: str
