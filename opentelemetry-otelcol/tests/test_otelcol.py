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

import os
import signal
from textwrap import dedent
from threading import Thread
from time import sleep
from unittest import TestCase

from opentelemetry.otelcol import otelcolcontrib_main


def send_sigterm_thread(
    delay_seconds: float, sig: signal.Signals = signal.SIGTERM
) -> Thread:
    def target() -> None:
        sleep(delay_seconds)
        os.kill(os.getpid(), sig)

    return Thread(target=target)


class TestOtelCol(TestCase):
    def test_otelcolmain(self) -> None:
        collector_config = dedent(
            """
            receivers:
              otlp:
                protocols:
                  grpc:
                  http:

            processors:
              batch:

            exporters:
              otlp:
                endpoint: otelcol:4317

            extensions:
              health_check:
              pprof:
              zpages:

            service:
              extensions: [health_check, pprof, zpages]
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

        thread = send_sigterm_thread(1)
        thread.start()
        otelcolcontrib_main(collector_config)
        thread.join()
