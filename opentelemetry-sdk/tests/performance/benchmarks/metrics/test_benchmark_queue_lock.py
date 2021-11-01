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


import time
from contextlib import contextmanager
from typing import Callable, Iterable
import pytest
from pytest_benchmark.fixture import BenchmarkFixture
from threading import Lock, Thread, Event
import queue


class LockCounter:
    def __init__(self) -> None:
        self.lock = Lock()
        self.count = 0

    def add(self, val: int) -> None:
        with self.lock:
            self.count += val

    def reset(self) -> None:
        with self.lock:
            self.count = 0

    def value(self) -> int:
        with self.lock:
            return self.count


class QueueCounter:
    def __init__(self) -> None:
        self.queue = queue.Queue(1000)
        self.count = 0
        self._shutdown = False
        self.consumer = Thread(target=self._consumer)
        self.consumer.start()

    def add(self, val: int) -> None:
        self.queue.put(val)

    def _consumer(self) -> None:
        while not self._shutdown:
            try:
                item = self.queue.get(timeout=0.1)
                self.count += item
                self.queue.task_done()
            except queue.Empty:
                pass

    def reset(self) -> None:
        self.count = 0

    def value(self) -> int:
        return self.count

    def flush(self) -> None:
        self.queue.join()

    def shutdown(self) -> None:
        self.flush()
        self._shutdown = True
        self.consumer.join()


@contextmanager
def contention(
    f: Callable[[], None], num_threads: int = 10, warmup_time: float = 0.5
) -> Iterable[None]:
    stop = False

    def target() -> None:
        while not stop:
            f()

    ts = [Thread(target=target) for _ in range(num_threads)]
    for t in ts:
        t.start()
    time.sleep(warmup_time)

    try:
        yield
    finally:
        stop = True
        for t in ts:
            t.join()


THREAD_RANGE = 4


@pytest.mark.parametrize("nthreads", range(THREAD_RANGE))
def test_benchmark_lock(benchmark: BenchmarkFixture, nthreads: int) -> None:
    # counter = LockCounter()

    # def f() -> None:
    #     counter.add(1)

    # with contention(f, num_threads=nthreads):
    #     benchmark(f)

    mu = Lock()
    count = 0

    def f() -> None:
        nonlocal count
        with mu:
            count += 1

    with contention(f, num_threads=nthreads):
        benchmark(f)


@pytest.mark.parametrize("nthreads", range(THREAD_RANGE))
def test_benchmark_lockless(
    benchmark: BenchmarkFixture, nthreads: int
) -> None:
    count = 0

    def f() -> None:
        nonlocal count
        count += 1

    with contention(f, num_threads=nthreads):
        benchmark(f)


@pytest.mark.parametrize("nthreads", range(THREAD_RANGE))
def test_benchmark_queue(benchmark: BenchmarkFixture, nthreads: int) -> None:
    counter = QueueCounter()

    def f() -> None:
        # print(counter.queue.qsize())
        counter.add(1)

    with contention(f, num_threads=nthreads):
        benchmark(f)

    counter.shutdown()
