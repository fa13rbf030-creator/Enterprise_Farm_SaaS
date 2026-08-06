from datetime import date
from decimal import Decimal
from uuid import uuid4

from finance_service.core.enums import (
    FraudCheckStatus,
    TreasuryFileFormat,
)
from finance_service.schemas.treasury import (
    TreasuryPaymentBatchCreate,
    TreasuryPaymentItemCreate,
)
from finance_service.services.treasury_calculations import (
    calculate_liquidity_projection,
    calculate_payment_batch_total,
    evaluate_basic_payment_fraud,
)


def build_batch() -> TreasuryPaymentBatchCreate:
    return TreasuryPaymentBatchCreate(
        tenant_id=uuid4(),
        batch_number="TB-001",
        batch_date=date(2026, 8, 6),
        execution_date=date(2026, 8, 7),
        bank_account_id=uuid4(),
        file_format=TreasuryFileFormat.ISO20022_PAIN_001,
        created_by=uuid4(),
        items=[
            TreasuryPaymentItemCreate(
                line_number=1,
                payment_reference="PAY-001",
                beneficiary_name="Supplier One",
                beneficiary_account="00112233",
                amount=Decimal("1000"),
            ),
            TreasuryPaymentItemCreate(
                line_number=2,
                payment_reference="PAY-002",
                beneficiary_name="Supplier Two",
                beneficiary_account="00445566",
                amount=Decimal("500"),
            ),
        ],
    )


def test_payment_batch_total() -> None:
    total, count = calculate_payment_batch_total(
        build_batch()
    )

    assert total == Decimal("1500.00")
    assert count == 2


def test_liquidity_projection_and_gap() -> None:
    closing, gap = calculate_liquidity_projection(
        opening_cash=Decimal("1000"),
        expected_inflows=Decimal("500"),
        expected_outflows=Decimal("1300"),
        minimum_cash_buffer=Decimal("500"),
    )

    assert closing == Decimal("200.00")
    assert gap == Decimal("300.00")


def test_duplicate_reference_is_blocked() -> None:
    status, reason = evaluate_basic_payment_fraud(
        amount=Decimal("100"),
        duplicate_reference=True,
        beneficiary_changed=False,
        daily_limit=Decimal("1000"),
    )

    assert status == FraudCheckStatus.BLOCKED
    assert reason == "Duplicate payment reference"


def test_large_payment_requires_review() -> None:
    status, _reason = evaluate_basic_payment_fraud(
        amount=Decimal("2000"),
        duplicate_reference=False,
        beneficiary_changed=False,
        daily_limit=Decimal("1000"),
    )

    assert status == FraudCheckStatus.REVIEW_REQUIRED
