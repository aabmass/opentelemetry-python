package main

/*
#include <string.h>
struct CollectorInstance {
	// a 128 byte buffer to write an error message into
	char err[128];
	int handle;
};
*/
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
func OtelColContribMain(yaml *C.char, handle *C.struct_CollectorInstance) int {
	yamlUri := "yaml:" + C.GoString(yaml)
	if err := main2(yamlUri); err != nil {
		writeToCharBuf(handle.err[:], err.Error())
		return 1
	}
	handle.handle = 123
	return 0
}

func writeToCharBuf(buf []C.char, gostring string) {
	for i, b := range append([]byte(gostring), 0) {
		if i >= len(buf) {
			return
		}
		buf[i] = C.char(b)
	}
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
