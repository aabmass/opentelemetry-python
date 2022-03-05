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

import multiprocessing
import os

NUM_PROCESSES = int(os.environ.get("NUM_PROCESSES", 1))


def busy() -> None:
    i = 123
    j = 321
    while True:
        i = i * j
        j = j % i


if __name__ == "__main__":
    processes = []
    for _ in range(NUM_PROCESSES):
        process = multiprocessing.Process(target=busy)
        process.start()
        processes.append(process)

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        for process in processes:
            process.kill()
