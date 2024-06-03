export GOBIN = $(PWD)/.tools/
export PATH += :$(GOBIN)

# GOFLAGS += -gcflags=all="-N -l"

BUILDDIR = $(PWD)
OTELCOLCONTRIB_SO = $(BUILDDIR)/otelcolcontrib.so
OTELCOLCONTRIB = $(BUILDDIR)/otelcolcontrib

.PHONY: tools
install-tools: $(GOBIN)/builder

$(GOBIN)/builder:
	go install go.opentelemetry.io/collector/cmd/builder@v0.101.0

ocb: install-tools
	builder --skip-compilation --config=ocb-manifest.yaml

.PHONY: sharedobject
sharedobject: $(OTELCOLCONTRIB_SO)
$(OTELCOLCONTRIB_SO): ocb
	cd go && \
		go build $(GOFLAGS) -buildmode=c-shared -o $(OTELCOLCONTRIB_SO)


.PHONY: otelcolcontrib
otelcolcontrib: $(OTELCOLCONTRIB)
$(OTELCOLCONTRIB): ocb
	cd go && \
		go build $(GOFLAGS) -o $(OTELCOLCONTRIB)
