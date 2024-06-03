package main

import "C"

import (
	"go.opentelemetry.io/collector/component"
	"go.opentelemetry.io/collector/confmap"
	"go.opentelemetry.io/collector/confmap/converter/expandconverter"
	envprovider "go.opentelemetry.io/collector/confmap/provider/envprovider"
	fileprovider "go.opentelemetry.io/collector/confmap/provider/fileprovider"
	httpprovider "go.opentelemetry.io/collector/confmap/provider/httpprovider"
	httpsprovider "go.opentelemetry.io/collector/confmap/provider/httpsprovider"
	yamlprovider "go.opentelemetry.io/collector/confmap/provider/yamlprovider"
	"go.opentelemetry.io/collector/otelcol"
)

//export OtelColContribMain
func OtelColContribMain(yaml *C.char) *C.char {
	yamlUri := "yaml:" + C.GoString(yaml)
	if err := main2(yamlUri); err != nil {
		return C.CString(err.Error())
	}
	return nil
}

func main2(yamlUri string) error {

	info := component.BuildInfo{
		Command:     "otelcol-contrib",
		Description: "OpenTelemetry Collector Contrib",
		Version:     "0.101.0",
	}

	set := otelcol.CollectorSettings{
		BuildInfo: info,
		Factories: components,
		ConfigProviderSettings: otelcol.ConfigProviderSettings{
			ResolverSettings: confmap.ResolverSettings{
				URIs: []string{yamlUri},
				ProviderFactories: []confmap.ProviderFactory{
					envprovider.NewFactory(),
					fileprovider.NewFactory(),
					httpprovider.NewFactory(),
					httpsprovider.NewFactory(),
					yamlprovider.NewFactory(),
				},
				ConverterFactories: []confmap.ConverterFactory{
					expandconverter.NewFactory(),
				},
			},
		},
	}

	return runInteractive2(set)
}

func runInteractive2(params otelcol.CollectorSettings) error {
	cmd := otelcol.NewCommand(params)
	// Unset args
	cmd.SetArgs([]string{})
	return cmd.Execute()
}
