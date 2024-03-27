python_requirements(
    name = "reqs",
    source = "pyproject.toml",
)

python_requirements(
    name = "reqs0",
    source = "test-requirements.txt",
)

# TODO: could generate tests for many python versions
# https://www.pantsbuild.org/2.19/docs/using-pants/key-concepts/targets-and-build-files#parametrizing-targets.
# Should work once interpreters are all installed on my system
# __defaults__({(python_test, python_tests): dict(
#     interpreter_constraints = parametrize(
#         py310 = ["==3.10.*"],
#         py311 = ["==3.11.*"],
#         py38 = ["==3.8.*"],
#         py39 = ["==3.9.*"],
#     ),
# )})
#
# When I tried this, it was a bit buggy.
