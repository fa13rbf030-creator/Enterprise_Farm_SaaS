from datetime import date, datetime, UTC
from decimal import Decimal
from uuid import uuid4

from finance_service.core.enums import (
    TreasuryFileFormat,
)
from finance_service.models.banking import BankAccount
from finance_service.models.treasury import (
    TreasuryPaymentBatch,
    TreasuryPaymentItem,
)
from finance_service.services.iso20022 import (
    generate_pain001_xml,
)


def test_generate_iso20022_pain001() -> None:
    batch = TreasuryPaymentBatch(
        id=uuid4(),
        tenant_id=uuid4(),
        batch_number="TB-001",
        batch_date=date(2026, 8, 6),
        execution_date=date(2026, 8, 7),
        bank_account_id=uuid4(),
        currency_code="PKR",
        total_amount=Decimal("1000"),
        item_count=1,
        file_format=(
            TreasuryFileFormat.ISO20022_PAIN_001
        ),
        created_by=uuid4(),
        created_at=datetime.now(UTC),
    )

    bank_account = BankAccount(
        id=batch.bank_account_id,
        tenant_id=batch.tenant_id,
        account_code="BANK-1",
        account_name="Main Account",
        bank_name="Example Bank",
        branch_name="Main",
        account_number="123456",
        iban="PK00EXAMPLE123456",
        swift_code="EXAMPKKA",
        currency_code="PKR",
        account_type="current",
        ledger_account_id=uuid4(),
        opening_balance=Decimal("0"),
        current_balance=Decimal("0"),
        created_by=uuid4(),
    )

    item = TreasuryPaymentItem(
        id=uuid4(),
        tenant_id=batch.tenant_id,
        batch_id=batch.id,
        line_number=1,
        payment_reference="PAY-001",
        beneficiary_name="Supplier",
        beneficiary_account="99999",
        beneficiary_iban="PK00SUPPLIER99999",
        amount=Decimal("1000"),
        currency_code="PKR",
    )

    xml, digest = generate_pain001_xml(
        batch=batch,
        bank_account=bank_account,
        items=[item],
    )

    assert "pain.001.001.03" in xml
    assert "PAY-001" in xml
    assert "PK00SUPPLIER99999" in xml
    assert len(digest) == 64
