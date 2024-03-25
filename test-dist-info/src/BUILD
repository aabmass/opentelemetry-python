# Infer dependencies from fakeimports.py
python_sources()

resources(
    name = "dist_info",
    # Transitively pull in dependencies
    dependencies = [":src"],
    sources = ["anyname.dist-info/**/*"],
)
