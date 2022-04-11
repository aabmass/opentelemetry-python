# Copyright 2021 The OpenTelemetry Authors
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
from typing import Sequence

from opentelemetry.sdk.trace.export import (
    ReadableSpan,
    SpanExporter,
    SpanExportResult,
)

logger = logging.getLogger(__name__)


class Exporter(SpanExporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.warning("logging: inside of __init__!")

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        logger.warning("logging: inside of export()")
        print("print: inside of export()")
        raise Exception("Oh no this isn't working")
        return SpanExportResult.SUCCESS
