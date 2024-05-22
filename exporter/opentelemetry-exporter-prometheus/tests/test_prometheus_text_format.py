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

from typing import Callable, Iterable
from syrupy import SnapshotAssertion

import pytest
from prometheus_client import generate_latest

from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider


@pytest.fixture
def prometheus_metric_reader() -> PrometheusMetricReader:
    return PrometheusMetricReader(disable_target_info=True)


@pytest.fixture
def meter_provider(
    prometheus_metric_reader: PrometheusMetricReader,
) -> Iterable[MeterProvider]:
    mp = MeterProvider(metric_readers=[prometheus_metric_reader])
    yield mp
    mp.shutdown(timeout_millis=100)


@pytest.fixture
def get_prometheus_text(
    prometheus_metric_reader: PrometheusMetricReader,
) -> Callable[[], str]:
    def result() -> str:
        result_bytes = generate_latest(prometheus_metric_reader._collector)
        return result_bytes.decode("utf-8").strip()

    return result


@pytest.mark.parametrize(
    "counter_name,unit",
    [("my.counter.name", "s"), ("request.count", "{requests}")],
)
def test_counter(
    counter_name: str,
    unit: str,
    meter_provider: MeterProvider,
    get_prometheus_text: Callable[[], str],
    snapshot: SnapshotAssertion,
) -> None:
    counter = meter_provider.get_meter("scope").create_counter(
        counter_name, unit=unit, description="My description"
    )
    counter.add(10, {"foo1.bar:baz": "hello world"})
    assert get_prometheus_text() == snapshot


def test_counter2(
    meter_provider: MeterProvider,
    get_prometheus_text: Callable[[], str],
    snapshot: SnapshotAssertion,
) -> None:
    counter = meter_provider.get_meter("scope").create_counter(
        "test.with.collision", unit="1", description="My description"
    )
    counter.add(
        1, {"hello_world": "hello_world", "hello.world": "hello.world"}
    )
    assert get_prometheus_text() == snapshot
