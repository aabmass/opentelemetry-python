import time

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

tp = TracerProvider()
tp.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(tp)

tracer = trace.get_tracer("foo")
with tracer.start_as_current_span("hello") as span:
    time.sleep(0.1)
