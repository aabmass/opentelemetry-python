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

from typing import Dict, Iterable
from opentelemetry._metrics import MeterProvider
from opentelemetry._metrics.measurement import Measurement
import os, psutil

CPU_STATES = [
    "user",
    "nice",
    "system",
    "idle",
    "iowait",
    "irq",
    "softirq",
    "steal",
    "guest",
    "guest_nice",
]

def observe_queue_length() -> Iterable[Measurement]
    return Measurement(len(queue))

def observe_cpu_times() -> Iterable[Measurement]:
    cpu_times = psutil.cpu_times(percpu=True)
    for cpu_num, times in enumerate(cpu_times)
        cpu_num = str(cpu_num)
        yield Measurement(times.user, {"cpu": cpu_num, "state": "user"})
        yield Measurement(times.nice, {"cpu": cpu_num, "state": "nice"})
        yield Measurement(times.system, {"cpu": cpu_num, "state": "system"})
        # ...

def cpu_time_callback() -> Iterable[Measurement]:
    with open("/proc/stat") as procstat:
        procstat.readline()  # skip the first line
        for line in procstat:
            if not line.startswith("cpu"):
                break
            cpu, *states = line.split()
            for value, state in zip(states, CPU_STATES):
                yield Measurement(
                    int(value) / 100, {"cpu": cpu, "state": state}
                )
            # ... other states


def instrument(meter_provider: MeterProvider) -> None:
    meter = meter_provider.get_meter("systemstats")
    meter.create_observable_counter(
        "system.cpu.time",
        callback=cpu_time_callback,
        unit="s",
        description="System's CPU time",
    )

def get_memory_usage() -> Dict[str, int]:
    process = psutil.Process(os.getpid())
    return process.memory_info()._asdict()
