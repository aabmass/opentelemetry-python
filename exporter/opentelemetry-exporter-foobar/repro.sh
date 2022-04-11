#!/bin/bash

python3 -m venv venv
source venv/bin/activate
pip install \
 -e . \
 -e ../../opentelemetry-api \
 -e ../../opentelemetry-sdk \
 opentelemetry-distro \
 opentelemetry-instrumentation \

opentelemetry-instrument \
	--log_level 0 \
	--logs_exporter console \
	--traces_exporter foobar \
	python -c 'from opentelemetry.trace import get_tracer; import time; span = get_tracer("test").start_span("testspan"); time.sleep(0.1); span.end();'
