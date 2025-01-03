load("@my_deps//:requirements.bzl", "requirement")
load("@rules_python//python:py_binary.bzl", "py_binary")

py_binary(
    name = "main",
    srcs = ["main.py"],
    deps = [
        requirement("opentelemetry-api"),
        requirement("opentelemetry-sdk"),
    ],
)
