from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.core.enums import (
    FinancialReportLineType,
    FinancialReportPeriodType,
    FinancialReportPresentation,
    FinancialReportType,
)
from finance_service.schemas.financial_reporting import (
    FinancialReportDefinitionCreate,
    FinancialReportLayoutCreate,
    FinancialReportLayoutLineCreate,
    FinancialReportRunCreate,
)


def test_layout_rejects_duplicate_line_codes() -> None:
    line = FinancialReportLayoutLineCreate(
        line_code="REV",
        line_name="Revenue",
        line_type=FinancialReportLineType.ACCOUNT,
    )

    with pytest.raises(ValidationError):
        FinancialReportLayoutCreate(
            layout_code="DEFAULT",
            layout_name="Default Layout",
            created_by=uuid4(),
            lines=[line, line],
        )


def test_definition_rejects_multiple_default_layouts() -> None:
    with pytest.raises(ValidationError):
        FinancialReportDefinitionCreate(
            tenant_id=uuid4(),
            report_code="IS",
            report_name="Income Statement",
            report_type=FinancialReportType.INCOME_STATEMENT,
            presentation_currency="PKR",
            created_by=uuid4(),
            layouts=[
                FinancialReportLayoutCreate(
                    layout_code="L1",
                    layout_name="Layout 1",
                    is_default=True,
                    created_by=uuid4(),
                ),
                FinancialReportLayoutCreate(
                    layout_code="L2",
                    layout_name="Layout 2",
                    is_default=True,
                    created_by=uuid4(),
                ),
            ],
        )


def test_report_run_rejects_invalid_period() -> None:
    with pytest.raises(ValidationError):
        FinancialReportRunCreate(
            tenant_id=uuid4(),
            definition_id=uuid4(),
            layout_id=uuid4(),
            run_number="RUN-1",
            period_type=FinancialReportPeriodType.MONTH,
            period_start=date(2026, 8, 31),
            period_end=date(2026, 8, 1),
            presentation=(
                FinancialReportPresentation.SINGLE_PERIOD
            ),
            presentation_currency="PKR",
            requested_by=uuid4(),
        )
