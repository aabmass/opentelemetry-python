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
import time
from typing import Callable, Iterable
from opentelemetry._metrics import get_meter, set_meter_provider

from opentelemetry._metrics.measurement import Measurement

from cpu_time import instrument
import worker

from prometheus_client import start_http_server

from opentelemetry.exporter.otlp.proto.grpc._metric_exporter import (
    OTLPMetricExporter,
)
from fastapi import FastAPI, Request

from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._metrics import MeterProvider
from opentelemetry.sdk._metrics.export import PeriodicExportingMetricReader

start_http_server(port=8000, addr="localhost")
prom_reader = PrometheusMetricReader()
otlp_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(), export_interval_millis=10_000
)

meter_provider = MeterProvider(
    metric_readers=[prom_reader, otlp_reader],
    resource=Resource.create({"service.name": "helloservice"}),
)
set_meter_provider(meter_provider)

# start our CPU stats
instrument(meter_provider)

meter = get_meter("myapp")

# Create a counter
orders_processed = meter.create_counter(
    "orders_processed",
    description="Number of orders processed",
)

request_duration = meter.create_histogram(
    "request.duration", unit="s", description="Duration of each request"
)


def make_task_count_callback(
    loop: asyncio.BaseEventLoop,
) -> Callable[[], Iterable[Measurement]]:
    def task_count_callback() -> Iterable[Measurement]:
        num_tasks = len(asyncio.all_tasks(loop))
        print(f"{num_tasks=}")
        yield Measurement(num_tasks)

    return task_count_callback


meter.create_observable_gauge(
    "runtime.asyncio.task_count",
    make_task_count_callback(asyncio.get_event_loop),
    description="Number of asyncio tasks currently running",
)

app = FastAPI()


@app.get("/hello")
async def hello():
    print(asyncio.get_event_loop())
    await worker.do_hello_work()
    orders_processed.add(1, {"region": "west"})
    return {"message": "Hello World"}


@app.get("/foo")
async def foo():
    await asyncio.gather(
        worker.do_hello_work(),
        worker.do_foo_work(),
    )
    orders_processed.add(2, {"region": "east"})
    return {"message": "bar"}


# Instrument request duration
@app.middleware("http")
async def record_duration(request: Request, call_next) -> None:
    start = time.time_ns()
    try:
        return await call_next(request)
    finally:
        end = time.time_ns()
        request_duration.record(
            (end - start) / 1e9, {"path": request.base_url.path}
        )
