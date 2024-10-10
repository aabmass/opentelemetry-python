import gc
import logging
import weakref

from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics._internal.export import (
    PeriodicExportingMetricReader,
)

logging.basicConfig(level=logging.DEBUG)


def create_and_clean():
    # setup_otlp_exporter
    otlp_exporter = OTLPMetricExporter(
        endpoint="http://localhost:4318/v1/metrics"
    )
    otlp_exporter_weakref = weakref.ref(otlp_exporter)

    reader = PeriodicExportingMetricReader(
        otlp_exporter, export_interval_millis=5000
    )
    reader_weakref = weakref.ref(reader)

    provider = MeterProvider(metric_readers=[reader])
    provider_weakref = weakref.ref(provider)

    provider.shutdown()
    return otlp_exporter_weakref, reader_weakref, provider_weakref


def check_referrers(wr, name):
    if wr() is not None:
        logging.warning("%s was not properly garbage collected", name)
        referrers = gc.get_referrers(wr())
        logging.debug(f"Direct referrers to %s: {len(referrers)}", name)
        for ref in referrers:
            logging.debug(f"%s referrer {str(ref)} type: {type(ref)}", name)
    else:
        logging.info("%s was properly garbage collected", name)


def main():
    otlp_exporter_weakref, reader_weakref, provider_weakref = (
        create_and_clean()
    )
    gc.collect()

    check_referrers(otlp_exporter_weakref, "OTLP EXPORTER")
    check_referrers(reader_weakref, "READER")
    check_referrers(provider_weakref, "PROVIDER")


if __name__ == "__main__":
    main()
