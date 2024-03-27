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

import contextlib
from typing import Callable, Iterator, TypeVar

from typing_extensions import ParamSpec

_T_co = TypeVar("_T_co", covariant=True)
_P = ParamSpec("_P")

# pylint: disable=protected-access
class _AgnosticContextManager(contextlib._GeneratorContextManager[_T_co]):

    """Context manager that can decorate both async and sync functions.

    This is an overridden version of the contextlib._GeneratorContextManager
    class that will decorate async functions with an async context manager
    to end the span AFTER the entire async function coroutine finishes.

    Else it will report near zero spans durations for async functions.

    We are overriding the contextlib._GeneratorContextManager class as
    reimplementing it is a lot of code to maintain and this class (even if it's
    marked as protected) doesn't seems like to be evolving a lot.

    For more information, see:
    https://github.com/open-telemetry/opentelemetry-python/pull/3633
    """

def _agnosticcontextmanager(
    func: Callable[_P, Iterator[_T_co]]
) -> Callable[_P, _AgnosticContextManager[_T_co]]: ...
