package main

import (
	"context"
	"encoding/json"
	"log"
	"os"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/stdout/stdoutmetric"
	"go.opentelemetry.io/otel/metric"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"

	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

func main() {
	// Create resource.
	res, err := resource.Merge(resource.Default(),
		resource.NewWithAttributes(semconv.SchemaURL,
			semconv.ServiceName("my-service"),
			semconv.ServiceVersion("0.1.0"),
		))
	if err != nil {
		log.Fatalln(err)
	}

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	exporter, err := stdoutmetric.New(
		stdoutmetric.WithEncoder(encoder),
	)
	if err != nil {
		log.Fatalln(err)
	}
	reader := sdkmetric.NewPeriodicReader(exporter)

	// Create a meter provider.
	// You can pass this instance directly to your instrumented code if it
	// accepts a MeterProvider instance.
	meterProvider := sdkmetric.NewMeterProvider(
		sdkmetric.WithResource(res),
		sdkmetric.WithReader(reader),
		sdkmetric.WithView(sdkmetric.NewView(
			sdkmetric.Instrument{Name: "*"},
			sdkmetric.Stream{Aggregation: sdkmetric.AggregationExplicitBucketHistogram{
				Boundaries: []float64{0, 10, 100, 1000},
			}},
		)),
	)

	// Handle shutdown properly so that nothing leaks.
	defer func() {
		err := meterProvider.Shutdown(context.Background())
		if err != nil {
			log.Fatalln(err)
		}
	}()

	// Register as global meter provider so that it can be used via otel.Meter
	// and accessed using otel.GetMeterProvider.
	// Most instrumentation libraries use the global meter provider as default.
	// If the global meter provider is not set then a no-op implementation
	// is used, which fails to generate data.
	otel.SetMeterProvider(meterProvider)

	_, err = otel.Meter("foo").Int64ObservableCounter(
		"observableCounter",
		metric.WithInt64Callback(callback),
	)
	if err != nil {
		log.Fatalln(err)
	}

	_, err = otel.Meter("foo").Int64ObservableGauge(
		"obseravableGauge",
		metric.WithInt64Callback(callback),
	)
	if err != nil {
		log.Fatalln(err)
	}
}

func callback(ctx context.Context, io metric.Int64Observer) error {
	io.Observe(12)
	io.Observe(112)
	io.Observe(1112)
	return nil
}
