from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from finance_service.models.intercompany import (
    ConsolidationGroupStatus,
    ConsolidationMemberMethod,
    ConsolidationPeriodStatus,
    IntercompanyRelationshipType,
    IntercompanyTransactionStatus,
)


class IntercompanyOrganizationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    organization_code: str = Field(min_length=1, max_length=50)
    organization_name: str = Field(min_length=1, max_length=255)
    base_currency: str = Field(min_length=3, max_length=3)


class IntercompanyOrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_code: str
    organization_name: str
    base_currency: str
    is_active: bool


class IntercompanyRelationshipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    parent_company_id: UUID
    child_company_id: UUID
    relationship_type: IntercompanyRelationshipType
    ownership_percentage: int = Field(ge=0, le=100)
    voting_percentage: int = Field(ge=0, le=100)
    effective_from: datetime
    effective_to: datetime | None = None

    @model_validator(mode="after")
    def validate_relationship(self):
        if self.parent_company_id == self.child_company_id:
            raise ValueError(
                "Parent and child companies must differ"
            )

        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "Relationship end cannot precede start"
            )

        return self


class IntercompanyRelationshipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    parent_company_id: UUID
    child_company_id: UUID
    relationship_type: IntercompanyRelationshipType
    ownership_percentage: int
    voting_percentage: int
    effective_from: datetime
    effective_to: datetime | None
    is_active: bool


class IntercompanyAccountMappingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    source_organization_id: UUID
    destination_organization_id: UUID
    source_due_from_account_id: UUID
    source_due_to_account_id: UUID
    destination_due_from_account_id: UUID
    destination_due_to_account_id: UUID
    settlement_currency: str = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_companies(self):
        if (
            self.source_organization_id
            == self.destination_organization_id
        ):
            raise ValueError(
                "Source and destination organizations must differ"
            )

        return self


class IntercompanyAccountMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    source_organization_id: UUID
    destination_organization_id: UUID
    source_due_from_account_id: UUID
    source_due_to_account_id: UUID
    destination_due_from_account_id: UUID
    destination_due_to_account_id: UUID
    settlement_currency: str
    is_active: bool


class ConsolidationGroupMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    consolidation_method: ConsolidationMemberMethod
    ownership_percentage: Decimal = Field(ge=0, le=100)
    voting_percentage: Decimal = Field(ge=0, le=100)
    effective_from: date
    effective_to: date | None = None


class ConsolidationGroupCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    group_code: str = Field(min_length=1, max_length=50)
    group_name: str = Field(min_length=1, max_length=255)
    parent_organization_id: UUID
    presentation_currency: str = Field(min_length=3, max_length=3)
    description: str = Field(default="", max_length=2000)
    created_by: UUID
    members: list[ConsolidationGroupMemberCreate] = Field(
        min_length=1
    )

    @model_validator(mode="after")
    def validate_members(self):
        organization_ids = [
            member.organization_id
            for member in self.members
        ]

        if len(organization_ids) != len(set(organization_ids)):
            raise ValueError(
                "Consolidation group members must be unique"
            )

        if self.parent_organization_id not in organization_ids:
            raise ValueError(
                "Parent organization must be included as member"
            )

        return self


class ConsolidationGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    group_code: str
    group_name: str
    parent_organization_id: UUID
    presentation_currency: str
    status: ConsolidationGroupStatus
    description: str
    created_by: UUID


class ConsolidationPeriodCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    group_id: UUID
    period_name: str = Field(min_length=1, max_length=100)
    period_start: date
    period_end: date
    presentation_currency: str = Field(min_length=3, max_length=3)
    opened_by: UUID

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError(
                "Consolidation period end cannot precede start"
            )

        return self


class ConsolidationPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    group_id: UUID
    period_name: str
    period_start: date
    period_end: date
    status: ConsolidationPeriodStatus
    presentation_currency: str
    opened_by: UUID
    closed_by: UUID | None
    closed_at: datetime | None


class IntercompanyTransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    transaction_number: str = Field(min_length=1, max_length=100)
    source_organization_id: UUID
    destination_organization_id: UUID
    transaction_date: date
    due_date: date | None = None
    currency_code: str = Field(min_length=3, max_length=3)
    amount: Decimal = Field(gt=0)
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)
    source_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    destination_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    created_by: UUID

    @model_validator(mode="after")
    def validate_transaction(self):
        if (
            self.source_organization_id
            == self.destination_organization_id
        ):
            raise ValueError(
                "Source and destination organizations must differ"
            )

        if (
            self.due_date is not None
            and self.due_date < self.transaction_date
        ):
            raise ValueError(
                "Due date cannot precede transaction date"
            )

        return self


class IntercompanyTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    transaction_number: str
    source_organization_id: UUID
    destination_organization_id: UUID
    transaction_date: date
    due_date: date | None
    currency_code: str
    amount: Decimal
    exchange_rate: Decimal
    base_amount: Decimal
    source_reference: str | None
    destination_reference: str | None
    status: IntercompanyTransactionStatus
    elimination_period_id: UUID | None
    created_by: UUID
