import asyncio
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    ConsoleSpanExporter,
)
import time

DURATION = 1.0

tp = TracerProvider()
tp.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(tp)
tracer = trace.get_tracer("tracer")


@tracer.start_as_current_span("foo_sync")
def foo_sync():
    time.sleep(DURATION)
    print("Hello world")


@tracer.start_as_current_span("foo_async")
async def foo_async():
    await asyncio.sleep(DURATION)
    print("Hello world")


foo_sync()
asyncio.run(foo_async(), debug=True)
