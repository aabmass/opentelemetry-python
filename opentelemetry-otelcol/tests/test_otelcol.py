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

from textwrap import dedent
from time import sleep
from unittest import TestCase

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.otelcol import Collector
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class TestOtelCol(TestCase):
    def test_otelcolmain(self) -> None:
        col = Collector(
            dedent(
                """
                receivers:
                  otlp:
                    protocols:
                      grpc:
                      http:

                processors:
                  batch:

                exporters:
                  debug:
                    verbosity: detailed
                  googlecloud:
                    project: ${env:PROJECT_ID}

                service:
                  pipelines:
                    traces:
                      receivers: [otlp]
                      processors: [batch]
                      exporters: [debug, googlecloud]
                    metrics:
                      receivers: [otlp]
                      processors: [batch]
                      exporters: [debug]
                    logs:
                      receivers: [otlp]
                      processors: [batch]
                      exporters: [debug]
                """
            )
        )

        tp = TracerProvider(
            resource=Resource.create({"service.name": "foobar"})
        )
        tp.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        with tp.get_tracer("foo").start_as_current_span("example-span"):
            sleep(0.1)
        tp.shutdown()
        col.shutdown()
