from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from finance_service.models.islamic_finance import (
    IslamicAssessmentStatus,
    IslamicAssessmentType,
    IslamicRuleStatus,
)


class ShariahRuleSetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    rule_code: str = Field(min_length=1, max_length=100)
    rule_name: str = Field(min_length=1, max_length=255)
    version_number: int = Field(default=1, ge=1)
    effective_from: date
    effective_to: date | None = None
    shariah_reference: str | None = Field(
        default=None,
        max_length=500,
    )
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "Rule-set end cannot precede start"
            )
        return self


class ShariahRuleSetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rule_code: str
    rule_name: str
    version_number: int
    status: IslamicRuleStatus
    effective_from: date
    effective_to: date | None
    shariah_reference: str | None
    approved_by: UUID | None
    approved_at: datetime | None
    notes: str


class ShariahRuleApprove(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    approved_by: UUID


class NisabReferenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    rule_set_id: UUID
    reference_date: date
    reference_type: str = Field(min_length=1, max_length=50)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    currency_code: str = Field(min_length=3, max_length=3)


class NisabReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rule_set_id: UUID
    reference_date: date
    reference_type: str
    quantity: Decimal
    unit_price: Decimal
    nisab_value: Decimal
    currency_code: str


class ZakatAssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    rule_set_id: UUID
    nisab_reference_id: UUID | None = None
    assessment_number: str = Field(min_length=1, max_length=100)
    assessment_date: date
    eligible_assets: Decimal = Field(ge=0)
    deductible_liabilities: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    nisab_value: Decimal = Field(ge=0)
    rate_percentage: Decimal = Field(ge=0, le=100)
    holding_days: int = Field(ge=0)
    required_hawl_days: int = Field(default=354, gt=0)
    prepared_by: UUID


class ZakatAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rule_set_id: UUID
    nisab_reference_id: UUID | None
    assessment_number: str
    assessment_date: date
    eligible_assets: Decimal
    deductible_liabilities: Decimal
    zakatable_base: Decimal
    nisab_value: Decimal
    rate_percentage: Decimal
    holding_days: int
    required_hawl_days: int
    zakat_due: Decimal
    status: IslamicAssessmentStatus
    prepared_by: UUID
    approved_by: UUID | None


class UshrAssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    rule_set_id: UUID
    assessment_number: str = Field(min_length=1, max_length=100)
    crop_batch_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    harvest_date: date
    irrigation_method: str = Field(min_length=1, max_length=100)
    eligible_output_value: Decimal = Field(ge=0)
    rate_percentage: Decimal = Field(ge=0, le=100)
    prepared_by: UUID


class UshrAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rule_set_id: UUID
    assessment_number: str
    crop_batch_reference: str | None
    harvest_date: date
    irrigation_method: str
    eligible_output_value: Decimal
    rate_percentage: Decimal
    ushr_due: Decimal
    status: IslamicAssessmentStatus
    prepared_by: UUID


class LivestockZakatRuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    rule_set_id: UUID
    species_code: str = Field(min_length=1, max_length=100)
    minimum_count: int = Field(ge=0)
    maximum_count: int | None = Field(default=None, ge=0)
    obligation_quantity: Decimal = Field(ge=0)
    obligation_unit: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def validate_range(self):
        if (
            self.maximum_count is not None
            and self.maximum_count < self.minimum_count
        ):
            raise ValueError(
                "Maximum livestock count cannot be below minimum"
            )
        return self


class SadaqahTransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    transaction_number: str = Field(min_length=1, max_length=100)
    transaction_date: date
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    beneficiary_reference: str | None = Field(
        default=None,
        max_length=255,
    )
    purpose: str = Field(default="", max_length=4000)
    recorded_by: UUID


class SadaqahTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    transaction_number: str
    transaction_date: date
    amount: Decimal
    currency_code: str
    beneficiary_reference: str | None
    purpose: str
    recorded_by: UUID


class IslamicDisbursementEvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    assessment_type: IslamicAssessmentType
    assessment_id: UUID | None = None
    evidence_number: str = Field(min_length=1, max_length=100)
    disbursement_date: date
    amount: Decimal = Field(gt=0)
    beneficiary_reference: str | None = Field(
        default=None,
        max_length=255,
    )
    document_reference: str | None = Field(
        default=None,
        max_length=500,
    )
    notes: str = Field(default="", max_length=4000)


class IslamicDisbursementEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    assessment_type: IslamicAssessmentType
    assessment_id: UUID | None
    evidence_number: str
    disbursement_date: date
    amount: Decimal
    beneficiary_reference: str | None
    document_reference: str | None
    notes: str
