package main

/*
struct CollectorInstance {
	// a 1024 byte buffer to write an error message into
	char err[1024];
	unsigned int handle;
};
*/
import "C"

import (
	"context"
	"errors"
	"fmt"
	"log"
	"math/rand"
	"sync"
	"time"

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
	mu                = sync.Mutex{}
	handlesToShutdown = map[C.uint]func(context.Context) error{}
)

//export NewCollector
func NewCollector(yaml *C.char, timeoutMillis uint) collectorInstance {
	mu.Lock()
	defer mu.Unlock()
	yamlUri := "yaml:" + C.GoString(yaml)
	inst := newCollectorInstance(nil)

	ctx := context.Background()
	if timeoutMillis > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(context.Background(), time.Millisecond*time.Duration(timeoutMillis))
		defer cancel()
	}

	shutdown, err := mainNonBlocking(ctx, yamlUri)
	if err != nil {
		inst.setError(err)
		return inst
	}

	handlesToShutdown[inst.handle] = shutdown

	return inst
}

//export ShutdownCollector
func ShutdownCollector(c collectorInstance, timeoutMillis uint) collectorInstance {
	mu.Lock()
	defer mu.Unlock()

	ctx := context.Background()
	if timeoutMillis > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(context.Background(), time.Millisecond*time.Duration(timeoutMillis))
		defer cancel()
	}

	log.Printf("Stopping collector handle ID: %v", c.handle)
	cancel, ok := handlesToShutdown[c.handle]
	if !ok {
		c.setError(fmt.Errorf("CollectorInstance with handle %v is not known", c.handle))
		return c
	}

	log.Printf("Got handle %v, cancel func %v", c.handle, cancel)
	c.setError(cancel(ctx))
	delete(handlesToShutdown, c.handle)
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
	for i, b = range append([]byte(gostring), 0) {
		if i == len(buf)-1 {
			// gostring too long, write null terminator
			buf[i] = 0
			return
		}
		buf[i] = C.char(b)
	}
}

var errTerminatedEarly = errors.New("collector terminated unexpectedly without error, check logs for details")

func mainNonBlocking(ctx context.Context, yamlUri string) (func(context.Context) error, error) {
	col, err := createOtelcol(ctx, yamlUri)
	if err != nil {
		return nil, err
	}

	done := make(chan error)
	// Run collector in background
	go func() {
		// run with detached context
		done <- col.Run(context.WithoutCancel(ctx))
	}()

	shutdown := func(ctx context.Context) error {
		log.Print("Starting shutdown")
		col.Shutdown()
		log.Print("Shutdown done")
		defer log.Print("Receiver return value in channel")
		select {
		case <-ctx.Done():
			return ctx.Err()
		case err := <-done:
			return err
		}
	}

	// Poll collector state until running. Unfortunately there is no channel to subscribe to
	// state changes
	ticker := time.NewTicker(time.Millisecond * 5)
	for col.GetState() == otelcol.StateStarting {
		select {
		case <-ticker.C:
		case <-ctx.Done():
			log.Printf("while waiting for collector to start: %v", ctx.Err().Error())
			return nil, fmt.Errorf("collector never entered running state (state=%v): %w", col.GetState(), ctx.Err())
		case err := <-done:
			if err != nil {
				return nil, err
			}
			return nil, errTerminatedEarly
		}
	}

	// check if passed Running
	if col.GetState() >= otelcol.StateClosing {
		err := <-done
		if err != nil {
			return nil, err
		}
		return nil, errTerminatedEarly
	}

	return shutdown, nil
}

func createOtelcol(ctx context.Context, yamlUri string) (*otelcol.Collector, error) {
	info := component.BuildInfo{
		Command:     "otelcol-contrib",
		Description: "OpenTelemetry Collector Contrib",
		Version:     "0.101.0",
	}

	set := otelcol.CollectorSettings{
		BuildInfo: info,
		Factories: components,
		// Let the python process handle gracefully shutting down
		DisableGracefulShutdown: true,
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

	col, err := otelcol.NewCollector(set)
	if err != nil {
		return nil, err
	}

	// Fail fast
	if err := col.DryRun(ctx); err != nil {
		return nil, err
	}
	return col, nil
}
