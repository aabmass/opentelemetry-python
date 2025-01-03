load("@api_deps//:requirements.bzl", "requirement")
load("@rules_python//python/entry_points:py_console_script_binary.bzl", "py_console_script_binary")

# This lets you run pytest
py_console_script_binary(
    name = "pytest",
    pkg = requirement("pytest"),
    visibility = ["//visibility:public"],
)

# exports_files([
#     "rules_python_entry_point_pytest.py",
# ])
