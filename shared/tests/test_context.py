from uuid import uuid4

from farm_shared.context import RequestContext


def test_request_context_is_tenant_scoped() -> None:
    tenant_id = uuid4()
    context = RequestContext(
        tenant_id=tenant_id,
        correlation_id="correlation-001",
    )

    assert context.tenant_id == tenant_id
    assert context.correlation_id == "correlation-001"
