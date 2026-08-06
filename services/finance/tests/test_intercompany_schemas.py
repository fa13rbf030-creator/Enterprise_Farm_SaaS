from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.models.intercompany import (
    ConsolidationMemberMethod,
    IntercompanyRelationshipType,
)
from finance_service.schemas.intercompany import (
    ConsolidationGroupCreate,
    ConsolidationGroupMemberCreate,
    IntercompanyRelationshipCreate,
    IntercompanyTransactionCreate,
)


def test_relationship_rejects_same_company() -> None:
    organization_id = uuid4()

    with pytest.raises(ValidationError):
        IntercompanyRelationshipCreate(
            tenant_id=uuid4(),
            parent_company_id=organization_id,
            child_company_id=organization_id,
            relationship_type=(
                IntercompanyRelationshipType.PARENT_SUBSIDIARY
            ),
            ownership_percentage=100,
            voting_percentage=100,
            effective_from=datetime.now(timezone.utc),
        )


def test_group_requires_parent_as_member() -> None:
    with pytest.raises(ValidationError):
        ConsolidationGroupCreate(
            tenant_id=uuid4(),
            group_code="GROUP-1",
            group_name="Enterprise Group",
            parent_organization_id=uuid4(),
            presentation_currency="PKR",
            created_by=uuid4(),
            members=[
                ConsolidationGroupMemberCreate(
                    organization_id=uuid4(),
                    consolidation_method=(
                        ConsolidationMemberMethod.FULL
                    ),
                    ownership_percentage=Decimal("100"),
                    voting_percentage=Decimal("100"),
                    effective_from=date(2026, 1, 1),
                )
            ],
        )


def test_transaction_rejects_invalid_due_date() -> None:
    with pytest.raises(ValidationError):
        IntercompanyTransactionCreate(
            tenant_id=uuid4(),
            transaction_number="IC-1",
            source_organization_id=uuid4(),
            destination_organization_id=uuid4(),
            transaction_date=date(2026, 8, 7),
            due_date=date(2026, 8, 6),
            currency_code="PKR",
            amount=Decimal("1000"),
            created_by=uuid4(),
        )
