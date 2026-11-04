# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

# pyright: reportIncompatibleMethodOverride=false
# pylint: disable=arguments-differ,no-self-use,unexpected-keyword-arg

"""Tests for the API ABC signature evolution policy and its compatibility shim."""

import inspect
import unittest
from collections.abc import Callable, Sequence
from typing import Any

from opentelemetry import _logs, metrics, trace
from opentelemetry import context as context_api
from opentelemetry._logs import Logger, LoggerProvider, LogRecord, SeverityNumber
from opentelemetry.metrics import (
    CallbackT,
    Counter,
    Histogram,
    Meter,
    MeterProvider,
    NoOpCounter,
    NoOpHistogram,
    NoOpObservableCounter,
    NoOpObservableGauge,
    NoOpObservableUpDownCounter,
    NoOpUpDownCounter,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.metrics._internal.instrument import Gauge
from opentelemetry.propagators import textmap
from opentelemetry.util._compat import SignatureCompatABC
from opentelemetry.util.types import Attributes

# Positional (positional-only or positional-or-keyword) parameters of every
# public method on the API's abstract base classes, as of the introduction of
# the policy. Anything added later MUST be keyword-only with a default (see
# test_new_parameters_are_keyword_only below), so this table should only ever
# change when a new method is added.
_API_ABC_POSITIONAL_PARAMETERS: dict[type[SignatureCompatABC], dict[str, tuple[str, ...]]] = {
    trace.TracerProvider: {
        "get_tracer": (
            "self",
            "instrumenting_module_name",
            "instrumenting_library_version",
            "schema_url",
            "attributes",
        ),
    },
    trace.Tracer: {
        "start_span": (
            "self",
            "name",
            "context",
            "kind",
            "attributes",
            "links",
            "start_time",
            "record_exception",
            "set_status_on_exception",
        ),
        "start_as_current_span": (
            "self",
            "name",
            "context",
            "kind",
            "attributes",
            "links",
            "start_time",
            "record_exception",
            "set_status_on_exception",
            "end_on_exit",
        ),
    },
    trace.Span: {
        "end": ("self", "end_time"),
        "get_span_context": ("self",),
        "set_attributes": ("self", "attributes"),
        "set_attribute": ("self", "key", "value"),
        "add_event": ("self", "name", "attributes", "timestamp"),
        "add_link": ("self", "context", "attributes"),
        "update_name": ("self", "name"),
        "is_recording": ("self",),
        "set_status": ("self", "status", "description"),
        "record_exception": ("self", "exception", "attributes", "timestamp", "escaped"),
    },
    metrics.MeterProvider: {
        "get_meter": ("self", "name", "version", "schema_url", "attributes"),
    },
    metrics.Meter: {
        "create_counter": ("self", "name", "unit", "description"),
        "create_up_down_counter": ("self", "name", "unit", "description"),
        "create_observable_counter": ("self", "name", "callbacks", "unit", "description"),
        "create_histogram": ("self", "name", "unit", "description"),
        "create_gauge": ("self", "name", "unit", "description"),
        "create_observable_gauge": ("self", "name", "callbacks", "unit", "description"),
        "create_observable_up_down_counter": ("self", "name", "callbacks", "unit", "description"),
    },
    Counter: {"add": ("self", "amount", "attributes", "context")},
    UpDownCounter: {"add": ("self", "amount", "attributes", "context")},
    Histogram: {"record": ("self", "amount", "attributes", "context")},
    Gauge: {"set": ("self", "amount", "attributes", "context")},
    ObservableCounter: {},
    ObservableGauge: {},
    ObservableUpDownCounter: {},
    _logs.LoggerProvider: {
        "get_logger": ("self", "name", "version", "schema_url", "attributes"),
    },
    _logs.Logger: {
        "emit": ("self", "record"),
        "enabled": ("self",),
    },
    textmap.Getter: {
        "get": ("self", "carrier", "key"),
        "keys": ("self", "carrier"),
    },
    textmap.Setter: {
        "set": ("self", "carrier", "key", "value"),
    },
    textmap.TextMapPropagator: {
        "extract": ("self", "carrier", "context", "getter"),
        "inject": ("self", "carrier", "context", "setter"),
    },
}

_POLICY = (
    "New optional parameters on API abstract base class methods must be keyword-only (or **kwargs), have a default "
    "and be safe for an implementation to ignore. See opentelemetry/util/_compat.py."
)


def _public_functions(cls: type) -> dict[str, Callable[..., Any]]:
    return {name: fn for name, fn in cls.__dict__.items() if not name.startswith("_") and inspect.isfunction(fn)}


class TestAPIABCSignaturePolicy(unittest.TestCase):
    def test_new_parameters_are_keyword_only(self) -> None:
        for cls, expected_methods in _API_ABC_POSITIONAL_PARAMETERS.items():
            with self.subTest(cls=cls.__qualname__):
                actual_methods = _public_functions(cls)
                self.assertEqual(
                    set(actual_methods),
                    set(expected_methods),
                    f"Public methods of {cls.__qualname__} changed. Update _API_ABC_POSITIONAL_PARAMETERS. {_POLICY}",
                )
                for name, fn in actual_methods.items():
                    params = list(inspect.signature(fn).parameters.values())
                    positional = tuple(
                        p.name
                        for p in params
                        if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                    )
                    self.assertEqual(
                        positional,
                        expected_methods[name],
                        f"Positional parameters of {cls.__qualname__}.{name} changed. {_POLICY}",
                    )
                    for param in params:
                        self.assertNotEqual(
                            param.kind,
                            inspect.Parameter.VAR_POSITIONAL,
                            f"{cls.__qualname__}.{name} must not declare *args. {_POLICY}",
                        )
                        if param.kind is inspect.Parameter.KEYWORD_ONLY:
                            self.assertIsNot(
                                param.default,
                                inspect.Parameter.empty,
                                f"{cls.__qualname__}.{name}(*, {param.name}) must have a default. {_POLICY}",
                            )


class TestOutOfDateImplementations(unittest.TestCase):
    """End-to-end checks through the real API entry points with implementations that
    do not accept newer keyword-only parameters or ``**kwargs``."""

    def test_meter_predating_histogram_advisory(self) -> None:
        class LegacyMeter(Meter):
            def __init__(self, name: str) -> None:
                super().__init__(name)
                self.histograms: list[tuple[str, str, str]] = []

            # Predates explicit_bucket_boundaries_advisory
            def create_histogram(self, name: str, unit: str = "", description: str = "") -> Histogram:
                self.histograms.append((name, unit, description))
                return NoOpHistogram(name, unit=unit, description=description)

            def create_counter(self, name: str, unit: str = "", description: str = "", **kwargs: Any) -> Counter:
                return NoOpCounter(name, unit=unit, description=description)

            def create_up_down_counter(
                self, name: str, unit: str = "", description: str = "", **kwargs: Any
            ) -> UpDownCounter:
                return NoOpUpDownCounter(name, unit=unit, description=description)

            def create_observable_counter(
                self,
                name: str,
                callbacks: Sequence[CallbackT] | None = None,
                unit: str = "",
                description: str = "",
                **kwargs: Any,
            ) -> ObservableCounter:
                return NoOpObservableCounter(name, callbacks, unit=unit, description=description)

            def create_observable_gauge(
                self,
                name: str,
                callbacks: Sequence[CallbackT] | None = None,
                unit: str = "",
                description: str = "",
                **kwargs: Any,
            ) -> ObservableGauge:
                return NoOpObservableGauge(name, callbacks, unit=unit, description=description)

            def create_observable_up_down_counter(
                self,
                name: str,
                callbacks: Sequence[CallbackT] | None = None,
                unit: str = "",
                description: str = "",
                **kwargs: Any,
            ) -> ObservableUpDownCounter:
                return NoOpObservableUpDownCounter(name, callbacks, unit=unit, description=description)

        class LegacyMeterProvider(MeterProvider):
            def __init__(self) -> None:
                self.meters: dict[str, LegacyMeter] = {}

            def get_meter(
                self,
                name: str,
                version: str | None = None,
                schema_url: str | None = None,
                attributes: Attributes = None,
            ) -> Meter:
                meter = self.meters.setdefault(name, LegacyMeter(name))
                return meter

        self.assertTrue(hasattr(LegacyMeter.create_histogram, "__wrapped__"))
        self.assertFalse(hasattr(LegacyMeter.create_counter, "__wrapped__"))

        provider = LegacyMeterProvider()
        meter = metrics.get_meter("my.service", meter_provider=provider)
        histogram = meter.create_histogram(
            "http.server.duration",
            unit="ms",
            description="Request duration",
            explicit_bucket_boundaries_advisory=[5.0, 10.0, 25.0, 100.0],
        )
        self.assertIsInstance(histogram, NoOpHistogram)
        self.assertEqual(
            provider.meters["my.service"].histograms,
            [("http.server.duration", "ms", "Request duration")],
        )

    def test_logger_predating_newer_keyword_only_fields(self) -> None:
        class LegacyLogger(Logger):
            def __init__(self, name: str) -> None:
                super().__init__(name)
                self.enabled_calls: list[SeverityNumber | None] = []
                self.emitted: list[tuple[Any, SeverityNumber | None]] = []

            # Predates `exception`
            def emit(
                self,
                record: LogRecord | None = None,
                *,
                timestamp: int | None = None,
                observed_timestamp: int | None = None,
                context: context_api.Context | None = None,
                severity_number: SeverityNumber | None = None,
                severity_text: str | None = None,
                body: Any = None,
                attributes: Attributes = None,
                event_name: str | None = None,
            ) -> None:
                self.emitted.append((body, severity_number))

            # Predates `event_name`
            def enabled(
                self,
                *,
                context: context_api.Context | None = None,
                severity_number: SeverityNumber | None = None,
            ) -> bool:
                self.enabled_calls.append(severity_number)
                return True

        class LegacyLoggerProvider(LoggerProvider):
            def __init__(self) -> None:
                self.loggers: dict[str, LegacyLogger] = {}

            def get_logger(
                self,
                name: str,
                version: str | None = None,
                schema_url: str | None = None,
                attributes: Attributes = None,
            ) -> Logger:
                return self.loggers.setdefault(name, LegacyLogger(name))

        self.assertTrue(hasattr(LegacyLogger.enabled, "__wrapped__"))
        self.assertTrue(hasattr(LegacyLogger.emit, "__wrapped__"))

        provider = LegacyLoggerProvider()
        logger = _logs.get_logger("my.service", logger_provider=provider)
        self.assertTrue(
            logger.enabled(
                context=context_api.get_current(),
                severity_number=SeverityNumber.INFO,
                event_name="user.login",
            )
        )
        # The rest of the log is still delivered when a newer field is dropped
        logger.emit(body="disk full", severity_number=SeverityNumber.ERROR, exception=RuntimeError("boom"))

        legacy = provider.loggers["my.service"]
        self.assertEqual(legacy.enabled_calls, [SeverityNumber.INFO])
        self.assertEqual(legacy.emitted, [("disk full", SeverityNumber.ERROR)])
