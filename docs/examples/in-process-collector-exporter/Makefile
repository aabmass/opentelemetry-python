SHELL := bash

build: out

out: venv wrapper.go
	source venv/bin/activate && \
		gopy build -output=out -vm=python3 .

venv:
	python3 -m venv venv
	venv/bin/python -m pip install -r requirements.txt

install-devdepends:
	go install golang.org/x/tools/cmd/goimports@latest
	go install github.com/go-python/gopy@latest

run: out
	venv/bin/python try_export.py

.PHONY: clean
clean:
	rm -rf out/ venv/
