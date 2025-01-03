load("@api_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_test")
load("@rules_python//python/entry_points:py_console_script_binary.bzl", "py_console_script_binary")

# This is cute, but it creates additinoal py_console_script_binary's genrule invocations for
# each of the macro. It would be better to cache the script that gets generated.
#
# Run `bazel query --output=build //opentelemetry-api:api_test` and notice that there is a
# one-off main script created for pytest
# "//opentelemetry-api:rules_python_entry_point_pytest.py".
def pytest_test(*, name, srcs = [], deps = [], main = None, **test_kwargs):
    """TODO"""

    if main != None:
        fail("Do not pass main to pytest_test, instead use py_test directly if you need main.")

    test_srcs = srcs
    test_deps = deps

    def py_test_wrapper(*, srcs, main, deps, **_):
        py_test(name = name, srcs = test_srcs + srcs, main = main, deps = test_deps + deps, **test_kwargs)

    py_console_script_binary(
        name = "pytest",
        binary_rule = py_test_wrapper,
        pkg = requirement("pytest"),
    )
