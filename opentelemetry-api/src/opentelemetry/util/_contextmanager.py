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

import inspect
from contextlib import (
    AbstractContextManager,
    contextmanager,
)
from functools import wraps
from typing import Any, Callable, Iterator, Optional, ParamSpec, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from contextlib import _GeneratorContextManager

P = ParamSpec("P")
T = TypeVar("T", covariant=True)

TDecorate = TypeVar("TDecorate", bound=Callable[..., Any])


def universal_contextmanager(
    generator_func: Callable[P, Iterator[T]]
) -> Callable[P, "_GeneratorContextManager[T]"]:
    """Like `contextmanager` but behaves in the expected way when decorating async functions

    When `contextmanager` is used as a `ContextDecorator` to decorate an async function, the
    underlying generator's code after the ``yield`` will be called immediately once Coroutine
    is returned. This means that the cleanup will run before the Coroutine even starts
    executing.

    `universal_contextmanager` behaves exactly the same as `contextmanager`, except it will
    await the Coroutine before running cleanup code in the wrapped generator.
    """
    sync_decorated = contextmanager(generator_func)

    class _UniversalContextManager(AbstractContextManager):
        def __init__(self, *args: P.args, **kwargs: P.kwargs) -> None:
            self.args = args
            self.kwargs = kwargs
            self.__sync: Optional[AbstractContextManager] = None

        @property
        def _sync(self) -> AbstractContextManager:
            if self.__sync is None:
                self.__sync = sync_decorated(*self.args, **self.kwargs)
            return self.__sync

        def __getattr__(self, name: str):
            return getattr(self._sync, name)

        def __enter__(self):
            return self._sync.__enter__()

        def __exit__(self, typ, value, traceback):
            return self._sync.__exit__(typ, value, traceback)

        def __call__(
            self,
            func_decorate: TDecorate,
        ) -> TDecorate:
            if inspect.iscoroutinefunction(func_decorate):

                @wraps(func_decorate)
                async def async_wrapper(*args, **kwargs):
                    with sync_decorated(*self.args, **self.kwargs):
                        return await func_decorate(*args, **kwargs)

                return async_wrapper  # type: ignore
            return sync_decorated(*self.args, **self.kwargs)(func_decorate)

    def helper(*args: P.args, **kwargs: P.kwargs) -> "_UniversalContextManager":
        return _UniversalContextManager(*args, **kwargs)

    return helper
