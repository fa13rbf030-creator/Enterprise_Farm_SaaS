from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from finance_service.core.enums import (
    FinancialReportBasis,
    FinancialReportLineType,
    FinancialReportPeriodType,
    FinancialReportPresentation,
    FinancialReportStandard,
    FinancialReportStatus,
    FinancialReportType,
)


class FinancialReportLayoutLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_code: str = Field(min_length=1, max_length=100)
    line_name: str = Field(min_length=1, max_length=255)
    line_type: FinancialReportLineType
    display_order: int = Field(default=0, ge=0)
    parent_line_code: str | None = Field(
        default=None,
        max_length=100,
    )
    account_filter: dict | None = None
    formula_expression: str | None = None
    style_configuration: dict | None = None
    is_visible: bool = True


class FinancialReportLayoutCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layout_code: str = Field(min_length=1, max_length=100)
    layout_name: str = Field(min_length=1, max_length=255)
    version_number: int = Field(default=1, ge=1)
    is_default: bool = False
    created_by: UUID
    lines: list[FinancialReportLayoutLineCreate] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_lines(self):
        codes = [line.line_code for line in self.lines]

        if len(codes) != len(set(codes)):
            raise ValueError(
                "Report layout line codes must be unique"
            )

        known_codes = set(codes)

        for line in self.lines:
            if (
                line.parent_line_code is not None
                and line.parent_line_code not in known_codes
            ):
                raise ValueError(
                    "Parent report line code does not exist"
                )

            if line.parent_line_code == line.line_code:
                raise ValueError(
                    "Report line cannot be its own parent"
                )

        return self


class FinancialReportDefinitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    report_code: str = Field(min_length=1, max_length=100)
    report_name: str = Field(min_length=1, max_length=255)
    report_type: FinancialReportType
    reporting_standard: FinancialReportStandard = (
        FinancialReportStandard.IFRS
    )
    accounting_basis: FinancialReportBasis = (
        FinancialReportBasis.ACCRUAL
    )
    default_presentation: FinancialReportPresentation = (
        FinancialReportPresentation.SINGLE_PERIOD
    )
    presentation_currency: str = Field(min_length=3, max_length=3)
    description: str = Field(default="", max_length=4000)
    is_system: bool = False
    created_by: UUID
    layouts: list[FinancialReportLayoutCreate] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_layouts(self):
        layout_codes = [
            layout.layout_code
            for layout in self.layouts
        ]

        if len(layout_codes) != len(set(layout_codes)):
            raise ValueError(
                "Report layout codes must be unique"
            )

        default_count = sum(
            1
            for layout in self.layouts
            if layout.is_default
        )

        if default_count > 1:
            raise ValueError(
                "Only one default layout is allowed"
            )

        return self


class FinancialReportDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    report_code: str
    report_name: str
    report_type: FinancialReportType
    reporting_standard: FinancialReportStandard
    accounting_basis: FinancialReportBasis
    default_presentation: FinancialReportPresentation
    presentation_currency: str
    description: str
    is_system: bool
    is_active: bool
    created_by: UUID
    created_at: datetime


class FinancialReportLayoutRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    definition_id: UUID
    layout_code: str
    layout_name: str
    version_number: int
    is_default: bool
    is_active: bool
    created_by: UUID
    created_at: datetime


class FinancialReportRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    definition_id: UUID
    layout_id: UUID
    run_number: str = Field(min_length=1, max_length=100)
    period_type: FinancialReportPeriodType
    period_start: date
    period_end: date
    comparative_period_start: date | None = None
    comparative_period_end: date | None = None
    presentation: FinancialReportPresentation
    presentation_currency: str = Field(min_length=3, max_length=3)
    consolidation_group_id: UUID | None = None
    budget_id: UUID | None = None
    segment_filter: dict | None = None
    parameters: dict | None = None
    requested_by: UUID

    @model_validator(mode="after")
    def validate_periods(self):
        if self.period_end < self.period_start:
            raise ValueError(
                "Report period end cannot precede start"
            )

        if (
            self.comparative_period_start is None
            and self.comparative_period_end is not None
        ):
            raise ValueError(
                "Comparative period start is required"
            )

        if (
            self.comparative_period_start is not None
            and self.comparative_period_end is None
        ):
            raise ValueError(
                "Comparative period end is required"
            )

        if (
            self.comparative_period_start is not None
            and self.comparative_period_end is not None
            and self.comparative_period_end
            < self.comparative_period_start
        ):
            raise ValueError(
                "Comparative period end cannot precede start"
            )

        return self


class FinancialReportRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    definition_id: UUID
    layout_id: UUID
    run_number: str
    period_type: FinancialReportPeriodType
    period_start: date
    period_end: date
    comparative_period_start: date | None
    comparative_period_end: date | None
    presentation: FinancialReportPresentation
    presentation_currency: str
    consolidation_group_id: UUID | None
    budget_id: UUID | None
    segment_filter: dict | None
    status: FinancialReportStatus
    requested_by: UUID
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    parameters: dict | None


class FinancialReportSnapshotCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    run_id: UUID
    snapshot_number: str = Field(min_length=1, max_length=100)
    snapshot_data: dict
    document_reference: str | None = Field(
        default=None,
        max_length=500,
    )
    content_hash: str | None = Field(
        default=None,
        max_length=128,
    )
    generated_by: UUID
    is_final: bool = False


class FinancialReportSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    run_id: UUID
    snapshot_number: str
    snapshot_data: dict
    document_reference: str | None
    content_hash: str | None
    generated_by: UUID
    generated_at: datetime
    is_final: bool


class FinancialDisclosureDefinitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    disclosure_code: str = Field(min_length=1, max_length=100)
    disclosure_name: str = Field(min_length=1, max_length=255)
    reporting_standard: FinancialReportStandard
    standard_reference: str | None = Field(
        default=None,
        max_length=255,
    )
    description: str = Field(default="", max_length=4000)
    data_requirements: dict | None = None
    is_mandatory: bool = False


class FinancialDisclosureDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    disclosure_code: str
    disclosure_name: str
    reporting_standard: FinancialReportStandard
    standard_reference: str | None
    description: str
    data_requirements: dict | None
    is_mandatory: bool
    is_active: bool
