load("@api_deps//:requirements.bzl", "requirement")
load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")
load("@rules_python//python:py_binary.bzl", "py_binary")
load("@rules_python//python:py_import.bzl", "py_import")
load("@rules_python//python:py_library.bzl", "py_library")
load("@rules_python//python:py_test.bzl", "py_test")
load("//tools:pytest_test.bzl", "pytest_test")

py_library(
    name = "api",
    srcs = glob(["src/**/*.py"]),
    imports = ["src/"],
    deps = [
        requirement("Deprecated"),
        requirement("importlib-metadata"),
    ],
)

py_package(
    name = "opentelemetry_api_pkg",
    packages = ["opentelemetry"],
    deps = [":api"],
)

py_wheel(
    name = "opentelemetry_api_wheel",
    # Package data. We're building "example_minimal_package-0.0.1-py3-none-any.whl"
    distribution = "opentelemetry-api",
    python_tag = "py3",
    strip_path_prefixes = ["opentelemetry-api/src"],
    version = "0.0.1",
    deps = [":opentelemetry_api_pkg"],
)

# This doesn't work, can I use whl_library?
py_import(
    name = "opentelemetry_api_wheel_lib",
    srcs = [":opentelemetry_api_wheel.dist"],
    deps = [],
)

py_binary(
    name = "foo",
    srcs = ["foo.py"],
    deps = [":opentelemetry_api_wheel_lib"],
)

pytest_test(
    name = "api_test",
    srcs = glob(["tests/**/*.py"]),
    deps = [":opentelemetry_api_wheel_lib"],
)
