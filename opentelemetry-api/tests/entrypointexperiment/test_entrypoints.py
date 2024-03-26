from opentelemetry.context import get_current
from opentelemetry.util._importlib_metadata import entry_points


def test_foo():
    eps = entry_points(
        group="opentelemetry_context", name="contextvars_context"
    )
    assert len(eps) > 0


def test_current():
    assert get_current() == {}


# contextvars_context
