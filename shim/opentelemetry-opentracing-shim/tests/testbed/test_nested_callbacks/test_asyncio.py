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

import asyncio

from ..otel_ot_shim_tracer import MockTracer
from ..testcase import OpenTelemetryTestCase
from ..utils import stop_loop_when


class TestAsyncio(OpenTelemetryTestCase):
    def setUp(self):  
        self.tracer = MockTracer()
        self.loop = asyncio.get_event_loop()

    def test_main(self):
        # Start a Span and let the callback-chain
        # finish it when the task is done
        async def task():
            with self.tracer.start_active_span("one", finish_on_close=False):
                self.submit()

        self.loop.create_task(task())

        stop_loop_when(
            self.loop,
            lambda: len(self.tracer.finished_spans()) == 1,
            timeout=5.0,
        )
        self.loop.run_forever()

        spans = self.tracer.finished_spans()
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].name, "one")

        for idx in range(1, 4):
            self.assertEqual(
                spans[0].attributes.get(f"key{idx}", None), str(idx)
            )

    def submit(self):
        span = self.tracer.scope_manager.active.span

        async def task1():
            span.set_tag("key1", "1")

            async def task2():
                span.set_tag("key2", "2")

                async def task3():
                    span.set_tag("key3", "3")
                    span.finish()

                self.loop.create_task(task3())

            self.loop.create_task(task2())

        self.loop.create_task(task1())
