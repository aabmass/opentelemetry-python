package main

/*
struct CollectorInstance {
	// a 128 byte buffer to write an error message into
	char err[128];
	unsigned int handle;
};
*/
import "C"

import (
	"context"
	"fmt"
	"math/rand"

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

var (
	handlesToCancel = map[C.uint]func() error{}
)

//export NewCollector
func NewCollector(yaml *C.char) collectorInstance {
	yamlUri := "yaml:" + C.GoString(yaml)
	inst := newCollectorInstance(nil)

	handlesToCancel[inst.handle] = mainNonBlocking(context.Background(), yamlUri)

	return inst
}

//export ShutdownCollector
func ShutdownCollector(c collectorInstance) collectorInstance {
	fmt.Printf("Stopping collector handle ID: %v\n", c.handle)
	cancel, ok := handlesToCancel[c.handle]
	if !ok {
		c.setError(fmt.Errorf("CollectorInstance with handle %v is not known", c.handle))
		return c
	}

	c.setError(cancel())
	delete(handlesToCancel, c.handle)
	return c
}

type collectorInstance C.struct_CollectorInstance

func newCollectorInstance(err error) collectorInstance {
	ret := collectorInstance{
		handle: C.uint(rand.Uint32()),
	}
	ret.setError(err)
	return ret
}

func (c *collectorInstance) setError(err error) {
	if err != nil {
		writeToCharBuf(c.err[:], err.Error())
	}
}

func writeToCharBuf(buf []C.char, gostring string) {
	var (
		i int
		b byte
	)
	for i, b = range []byte(gostring) {
		if i == len(buf)-1 {
			break
		}
		buf[i] = C.char(b)
	}
	// null terminate
	buf[i] = 0
}

func mainNonBlocking(ctx context.Context, yamlUri string) func() error {
	ctx, cancel := context.WithCancel(ctx)
	done := make(chan error)
	go func() {
		done <- main2(ctx, yamlUri)
	}()

	return func() error {
		cancel()
		return <-done
	}
}

func main2(ctx context.Context, yamlUri string) error {

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

	return runInteractive2(ctx, set)
}

func runInteractive2(ctx context.Context, params otelcol.CollectorSettings) error {
	cmd := otelcol.NewCommand(params)
	// Unset args
	cmd.SetArgs([]string{})
	return cmd.ExecuteContext(ctx)
}
