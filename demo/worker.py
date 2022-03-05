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
from numpy.random import default_rng

rng = default_rng()


async def do_foo_work() -> None:
    await _do_work()


async def do_hello_work() -> None:
    await _do_work()


async def _do_work() -> None:
    sl = rng.pareto(4) * 2
    print(f"Wait for {sl} seconds")
    await asyncio.sleep(sl)
