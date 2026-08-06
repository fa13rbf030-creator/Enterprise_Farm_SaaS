import pytest

from finance_service.services.fixed_assets import (
    FixedAssetWorkflowError,
)


def test_fixed_asset_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise FixedAssetWorkflowError(
            "fixed asset workflow failed"
        )
