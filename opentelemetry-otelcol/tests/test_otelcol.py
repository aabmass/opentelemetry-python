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

from opentelemetry.otelcol import Collector


class TestOtelCol(TestCase):
    def test_otelcolmain(self) -> None:
        col = Collector(
            dedent(
                """
                receivers:
                  otlp:
                    protocols:
                      grpc:
                    #   http:

                processors:
                  batch:

                exporters:
                  otlp:
                    endpoint: otelcol:4317

                service:
                  pipelines:
                    traces:
                      receivers: [otlp]
                      processors: [batch]
                      exporters: [otlp]
                    metrics:
                      receivers: [otlp]
                      processors: [batch]
                      exporters: [otlp]
                    logs:
                      receivers: [otlp]
                      processors: [batch]
                      exporters: [otlp]
                """
            )
        )
        sleep(1)
        col.shutdown()
