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
# otelcolcontrib.OtelColContribMain.restype = ctypes.c_char_p


class CollectorInstance(ctypes.Structure):
    _fields_ = [("err", ctypes.c_char * 128), ("handle", ctypes.c_int)]

    err: bytes
    handle: int


# otelcolcontrib.OtelColContribMain.restype = CollectorInstance


class CollectorException(Exception):
    pass


def otelcolcontrib_main(config_yaml: str) -> None:
    config_bytes = config_yaml.encode()

    inst = CollectorInstance()
    res: int = otelcolcontrib.OtelColContribMain(
        config_bytes, ctypes.pointer(inst)
    )
    print(f"Got {res=}, {inst.err=}, {inst.handle=}")
    if res:
        raise CollectorException(inst.err.decode())
