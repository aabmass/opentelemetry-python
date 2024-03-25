from opentelemetry.util._importlib_metadata import entry_points
from opentelemetry.context import get_current


def test_foo():
    eps = entry_points(
        group="opentelemetry_context", name="contextvars_context"
    )
    assert len(eps) > 0


def test_current():
    assert get_current() == {}


# contextvars_context
