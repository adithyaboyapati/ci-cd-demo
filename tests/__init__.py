# WHY A SEPARATE tests/__init__.py?
# This empty file tells Python that the tests/ directory is a package.
# It ensures pytest can import fixtures from conftest.py correctly
# regardless of where the test runner is invoked from.
# In CI, tests are always run from the project root — this file makes
# import resolution consistent across local dev and the CI container.
