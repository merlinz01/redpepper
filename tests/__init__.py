from typing import Any

import pytest


def get_param_from_request(
    request: pytest.FixtureRequest, name: str, default: Any = None
) -> Any:
    marker = request.node.get_closest_marker("fixture_params")
    if marker is None:
        return default
    return marker.kwargs.get(name, default)
