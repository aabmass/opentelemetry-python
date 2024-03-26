raise NotImplementedError(
    "Do not import this module, it is fake just for dependency inference"
)

import opentelemetry.environment_variables
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context.contextvars_context import ContextVarsRuntimeContext
from opentelemetry.metrics import NoOpMeterProvider
from opentelemetry.trace import NoOpTracerProvider
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
