from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.models.finance_analytics import (
    FinanceAnalyticsPeriodType,
)
from finance_service.schemas.finance_analytics import (
    FinanceAnalyticsSnapshotCreate,
)


def build_payload():
    return {
        "tenant_id": uuid4(),
        "snapshot_number": "CFO-2026-08",
        "period_type": FinanceAnalyticsPeriodType.MONTHLY,
        "period_start": date(2026, 8, 1),
        "period_end": date(2026, 8, 31),
        "currency_code": "pkr",
        "revenue": Decimal("1000"),
        "calculated_by": uuid4(),
    }


def test_snapshot_schema_normalizes_currency() -> None:
    payload = FinanceAnalyticsSnapshotCreate(
        **build_payload()
    )

    assert payload.currency_code == "PKR"


def test_snapshot_schema_rejects_invalid_period() -> None:
    data = build_payload()

    data["period_start"] = date(2026, 8, 31)
    data["period_end"] = date(2026, 8, 1)

    with pytest.raises(ValidationError):
        FinanceAnalyticsSnapshotCreate(
            **data
        )


def test_snapshot_schema_rejects_invalid_currency() -> None:
    data = build_payload()
    data["currency_code"] = "PK"

    with pytest.raises(ValidationError):
        FinanceAnalyticsSnapshotCreate(
            **data
        )


def test_snapshot_schema_requires_positive_days() -> None:
    data = build_payload()
    data["days_in_period"] = 0

    with pytest.raises(ValidationError):
        FinanceAnalyticsSnapshotCreate(
            **data
        )
