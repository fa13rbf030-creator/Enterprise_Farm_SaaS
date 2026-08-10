from procurement_service.main import app


EXPECTED_APPROVAL_PATHS = {
    "/approvals": {"post"},
    "/approvals/{request_id}": {"get"},
    "/approvals/{request_id}/cancel": {"post"},
    (
        "/approvals/{request_id}/steps/"
        "{step_number}/approve"
    ): {"post"},
    (
        "/approvals/{request_id}/steps/"
        "{step_number}/reject"
    ): {"post"},
}


def test_approval_openapi_paths_are_registered():
    document = app.openapi()

    actual = {
        path: set(
            document["paths"][path].keys()
        )
        for path in document.get("paths", {})
        if path.startswith("/approvals")
    }

    assert set(actual) == set(
        EXPECTED_APPROVAL_PATHS
    )

    for path, methods in (
        EXPECTED_APPROVAL_PATHS.items()
    ):
        assert methods <= actual[path]


def test_approval_openapi_has_five_paths():
    document = app.openapi()

    paths = {
        path
        for path in document.get("paths", {})
        if path.startswith("/approvals")
    }

    assert len(paths) == 5


def test_approval_operations_have_security_requirements():
    document = app.openapi()

    for path in EXPECTED_APPROVAL_PATHS:
        for operation in (
            document["paths"][path].values()
        ):
            assert operation.get("security")


def test_approval_create_requires_tenant_header():
    document = app.openapi()

    operation = document["paths"][
        "/approvals"
    ]["post"]

    parameters = {
        (
            parameter.get("name"),
            parameter.get("in"),
        )
        for parameter in operation.get(
            "parameters",
            []
        )
    }

    assert (
        "X-Tenant-ID",
        "header",
    ) in parameters


def test_approval_api_uses_bearer_security_scheme():
    document = app.openapi()

    schemes = (
        document
        .get("components", {})
        .get("securitySchemes", {})
    )

    assert schemes

    assert any(
        scheme.get("type") == "oauth2"
        for scheme in schemes.values()
    )
