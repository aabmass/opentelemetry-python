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

import logging

import ctypes
import pathlib

logger = logging.getLogger(__name__)

sopath = pathlib.Path(__file__).parent / "otelcolcontrib.so"
logger.info("Searching for dll/so at %s", sopath)
otelcolcontrib = ctypes.CDLL(str(sopath))


class CollectorException(Exception):
    pass


class _CollectorInstance(ctypes.Structure):
    _fields_ = [("err", ctypes.c_char * 128), ("handle", ctypes.c_uint32)]

    err: bytes
    handle: int

    def check_error(self) -> None:
        if self.err:
            raise CollectorException(self.err.decode())

    def __repr__(self) -> str:
        return f"_CollectorInstance(err={self.err}, handle={self.handle})"


otelcolcontrib.NewCollector.restype = _CollectorInstance
otelcolcontrib.ShutdownCollector.argtypes = [_CollectorInstance]
otelcolcontrib.ShutdownCollector.restype = _CollectorInstance


class Collector:
    def __init__(self, config_yaml: str) -> None:
        config_bytes = config_yaml.encode()

        self._inst: _CollectorInstance = otelcolcontrib.NewCollector(
            config_bytes
        )
        print(f"Got {self._inst}")
        self._inst.check_error()

    def shutdown(self) -> None:
        self._inst = otelcolcontrib.ShutdownCollector(self._inst)
        self._inst.check_error()
