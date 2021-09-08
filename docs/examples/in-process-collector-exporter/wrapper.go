package pythonexporter

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/open-telemetry/opentelemetry-collector-contrib/exporter/googlecloudexporter"
	"github.com/open-telemetry/opentelemetry-collector-contrib/exporter/jaegerexporter"
	"go.opentelemetry.io/collector/component"
	"go.opentelemetry.io/collector/component/componenttest"
	"go.opentelemetry.io/collector/config"
	"go.opentelemetry.io/collector/config/configparser"
	"go.opentelemetry.io/collector/model/otlp"
	"go.opentelemetry.io/otel/trace"
	"go.uber.org/zap"
)

type TraceExporter struct {
	texp   component.TracesExporter
	logger *zap.Logger
	type_  config.Type
}

// Creates a new google cloud trace exporter that can be used in python
func NewGooglecloudTraceExporter(configYaml string) (*TraceExporter, error) {
	return newTraceExporter(
		configYaml,
		googlecloudexporter.NewFactory(),
	)
}

func NewJaegerTraceExporter(configYaml string) (*TraceExporter, error) {
	return newTraceExporter(
		configYaml,
		jaegerexporter.NewFactory(),
	)
}

func newTraceExporter(
	configYaml string,
	exporterFactory component.ExporterFactory,
) (*TraceExporter, error) {
	ctx := context.Background()
	logger, err := zap.NewDevelopment()
	if err != nil {
		return nil, err
	}

	cfg, err := loadConfig(logger, configYaml, exporterFactory)
	if err != nil {
		return nil, err
	}

	texp, err := exporterFactory.CreateTracesExporter(
		ctx,
		component.ExporterCreateSettings{
			Logger:         logger,
			TracerProvider: trace.NewNoopTracerProvider(),
		},
		cfg,
	)
	if err != nil {
		return nil, err
	}

	if err := texp.Start(ctx, componenttest.NewNopHost()); err != nil {
		return nil, err
	}

	return &TraceExporter{
		texp:   texp,
		logger: logger,
		type_:  exporterFactory.Type(),
	}, nil
}

func loadConfig(
	logger *zap.Logger,
	configYaml string,
	exporterFactory component.ExporterFactory,
) (config.Exporter, error) {
	parser, err := configparser.NewParserFromBuffer(strings.NewReader(configYaml))
	if err != nil {
		return nil, err
	}

	cfg := exporterFactory.CreateDefaultConfig()
	if err := parser.Unmarshal(cfg); err != nil {
		return nil, err
	}

	logger.Sugar().Debugf("Config object:\n%+v", cfg)

	return cfg, nil
}

func (we *TraceExporter) Export(otlpTraceRequestBytes []byte, timeoutSeconds float64) error {
	timeout, err := time.ParseDuration(fmt.Sprintf("%vs", timeoutSeconds))
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(
		context.Background(),
		timeout,
	)
	defer cancel()
	sl := we.logger.Sugar()
	sl.Debugf("Entering Export() for wrapped exporter %v. Will timeout after %v", we.type_, timeout)

	tracesUnmarshaler := otlp.NewProtobufTracesUnmarshaler()
	traces, err := tracesUnmarshaler.UnmarshalTraces(otlpTraceRequestBytes)
	if err != nil {
		return err
	}
	sl.Debugf("Successfully unmarshaled protobuf, have %v spans to export", traces.SpanCount())

	err = we.texp.ConsumeTraces(ctx, traces)
	if err == nil {
		sl.Debugf("Export was successful")
	}
	return err
}

func (we *TraceExporter) Shutdown(timeoutSeconds float64) error {
	timeout, err := time.ParseDuration(fmt.Sprintf("%vs", timeoutSeconds))
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(
		context.Background(),
		timeout,
	)
	defer cancel()
	sl := we.logger.Sugar()
	sl.Debugf("Entering Shutdown() for wrapped exporter %v", we.type_)
	err = we.texp.Shutdown(ctx)
	if err == nil {
		sl.Debugf("Shutdown() was successful")
	}
	return err
}
