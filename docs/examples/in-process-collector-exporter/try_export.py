# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example using in process collector exporters

Run this example with ``make run``. You need a Go compiler, gopy binaries
(install with ``make install-devdepends``), C compiler, and python dev packages to link
against.

It will export traces to Google Cloud Trace (using the ``PROJECT_ID``
environment variable you pass in, or application default credentials) and
Jaeger. To run Jaeger locally, use the AIO docker image:

.. code-block:: bash
    docker run \
        --rm \
        --name jaeger \
        -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
        -p 5775:5775/udp \
        -p 6831:6831/udp \
        -p 6832:6832/udp \
        -p 5778:5778 \
        -p 16686:16686 \
        -p 14268:14268 \
        -p 14250:14250 \
        -p 9411:9411 \
        jaegertracing/all-in-one:1.26

Then load the Jaeger web UI at http://localhost:16686/
"""

import asyncio
import os
import random
from typing import Sequence

from opentelemetry.exporter.otlp.proto.http.trace_exporter.encoder import (
    _ProtobufEncoder,
)
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from out import pythonexporter


class WrappedExporterShimExporter(SpanExporter):
    def __init__(
        self,
        collectorExporter: pythonexporter.TraceExporter,
        timeout_sec: float = 5.0,
    ) -> None:
        self._collectorExporter = collectorExporter
        self._timeout_sec = timeout_sec

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        export_traces_req = _ProtobufEncoder.encode(spans)
        go_bytes = pythonexporter.go.Slice_byte(
            export_traces_req.SerializeToString()
        )
        self._collectorExporter.Export(go_bytes, self._timeout_sec)

    def shutdown(self) -> None:
        self._collectorExporter.Shutdown(self._timeout_sec)


tp = TracerProvider(sampler=TraceIdRatioBased(0.05))
tp.add_span_processor(
    BatchSpanProcessor(
        span_exporter=WrappedExporterShimExporter(
            pythonexporter.NewGooglecloudTraceExporter(
                f"""
project: "{os.environ.get('PROJECT_ID', '')}"
timeout: 5s
""",
            ),
        )
    )
)
tp.add_span_processor(
    BatchSpanProcessor(
        span_exporter=WrappedExporterShimExporter(
            pythonexporter.NewJaegerTraceExporter(
                """
endpoint: localhost:14250
insecure: true
""",
            ),
        )
    )
)

tracer = tp.get_tracer(__name__)


async def randsleep(max_sleep: float = 2.0) -> None:
    await asyncio.sleep(random.random() * max_sleep)


async def genspans(i: int, sem: asyncio.BoundedSemaphore) -> None:
    async with sem:
        with tracer.start_as_current_span("hello-root-python") as rootSpan:
            await randsleep()
            with tracer.start_as_current_span("hello-child") as span:
                await randsleep()
                span.set_attribute("helllo", "world")
                with tracer.start_as_current_span("child-child") as span:
                    await randsleep()
                    span.set_attribute("there", "foo")
            rootSpan.set_attribute("is.root", True)
            rootSpan.set_attribute("number", i)


async def main() -> None:
    sem = asyncio.BoundedSemaphore(100)
    await asyncio.gather(*(genspans(i, sem) for i in range(10000)))
    tp.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
