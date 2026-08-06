from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.schemas.treasury import (
    TreasuryPaymentBatchCreate,
    TreasuryPaymentItemCreate,
)


def test_execution_date_validation() -> None:
    with pytest.raises(ValidationError):
        TreasuryPaymentBatchCreate(
            tenant_id=uuid4(),
            batch_number="TB-INVALID",
            batch_date=date(2026, 8, 7),
            execution_date=date(2026, 8, 6),
            bank_account_id=uuid4(),
            created_by=uuid4(),
            items=[
                TreasuryPaymentItemCreate(
                    line_number=1,
                    payment_reference="PAY-X",
                    beneficiary_name="Vendor",
                    beneficiary_account="123",
                    amount=Decimal("100"),
                )
            ],
        )


def test_duplicate_line_numbers_rejected() -> None:
    with pytest.raises(ValidationError):
        TreasuryPaymentBatchCreate(
            tenant_id=uuid4(),
            batch_number="TB-DUP",
            batch_date=date(2026, 8, 6),
            execution_date=date(2026, 8, 7),
            bank_account_id=uuid4(),
            created_by=uuid4(),
            items=[
                TreasuryPaymentItemCreate(
                    line_number=1,
                    payment_reference="PAY-1",
                    beneficiary_name="Vendor A",
                    beneficiary_account="123",
                    amount=Decimal("100"),
                ),
                TreasuryPaymentItemCreate(
                    line_number=1,
                    payment_reference="PAY-2",
                    beneficiary_name="Vendor B",
                    beneficiary_account="456",
                    amount=Decimal("200"),
                ),
            ],
        )
