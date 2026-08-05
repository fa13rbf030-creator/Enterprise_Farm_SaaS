from uuid import uuid4

import pytest
from fastapi import HTTPException

from finance_service.api.gl import (
    validate_payload_tenant,
)


def test_matching_tenant_is_allowed() -> None:
    tenant_id = uuid4()

    validate_payload_tenant(
        header_tenant_id=tenant_id,
        payload_tenant_id=tenant_id,
    )


def test_mismatched_tenant_is_denied() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_payload_tenant(
            header_tenant_id=uuid4(),
            payload_tenant_id=uuid4(),
        )

    assert exc.value.status_code == 403
