raise NotImplementedError(
    "Do not import this module, it is fake just for dependency inference"
)

from opentelemetry.context.contextvars_context import ContextVarsRuntimeContext
import opentelemetry.environment_variables
from opentelemetry.metrics import NoOpMeterProvider
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
from opentelemetry.trace import NoOpTracerProvider
