from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.core.enums import CashPoolType
from finance_service.schemas.advanced_treasury import (
    CashPoolCreate,
    CashPoolMemberCreate,
    IntercompanyTransferCreate,
)


def test_cash_pool_rejects_header_as_member() -> None:
    account_id = uuid4()

    with pytest.raises(ValidationError):
        CashPoolCreate(
            tenant_id=uuid4(),
            pool_code="POOL-1",
            pool_name="Main Pool",
            pool_type=CashPoolType.PHYSICAL,
            header_bank_account_id=account_id,
            currency_code="PKR",
            created_by=uuid4(),
            members=[
                CashPoolMemberCreate(
                    bank_account_id=account_id,
                )
            ],
        )


def test_transfer_rejects_same_account() -> None:
    account_id = uuid4()

    with pytest.raises(ValidationError):
        IntercompanyTransferCreate(
            tenant_id=uuid4(),
            transfer_number="TR-1",
            transfer_date=date(2026, 8, 6),
            source_bank_account_id=account_id,
            destination_bank_account_id=account_id,
            amount=Decimal("100"),
            currency_code="PKR",
            created_by=uuid4(),
        )
