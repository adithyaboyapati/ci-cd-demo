"""
tests/conftest.py — pytest Fixtures
=====================================

WHAT IS A FIXTURE?
A fixture is setup/teardown code that pytest runs before/after each test.
Think of it as the "arrange" step in the Arrange-Act-Assert pattern.

WHY THIS MATTERS FOR CI/CD:
The CI pipeline runs ALL tests in sequence. Without fixtures:
  - Test A creates a task
  - Test B expects zero tasks, but finds one → FAILS
  - The build breaks for the wrong reason
  - Engineers waste time debugging a "ghost" failure

With our reset fixture, each test starts with a clean slate — guaranteed.
This is called "test isolation" and it's non-negotiable for reliable CI.

FIXTURE SCOPES:
  - function (default): runs before EVERY test — most isolated
  - module: runs once per test file — faster but less isolated
  - session: runs once per test run — fastest, but no isolation

We use function scope here for maximum reliability.
"""

import pytest
from app import create_app
from app.models import store


@pytest.fixture(scope="session")
def app():
    """
    Create the Flask application configured for testing.

    WHY session scope?
    Creating the Flask app is slightly expensive. We create it ONCE per
    test session and reuse it. The store is reset between tests (see below),
    so reusing the app object is safe.

    The 'testing' config enables:
      - TESTING = True  → exceptions propagate (no silent swallowing)
      - No real external dependencies (no real DB, no real email)
    """
    flask_app = create_app("testing")
    yield flask_app


@pytest.fixture(scope="session")
def client(app):
    """
    Flask test client — makes HTTP requests without a real server.

    WHY: This lets our CI pipeline run tests without:
      - Binding to a real network port
      - Starting a real HTTP server process
      - Worrying about port conflicts between parallel test runs

    The test client simulates HTTP requests at the WSGI layer — it's fast,
    deterministic, and completely self-contained.
    """
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_store():
    """
    Reset the task store before EVERY test.

    WHY autouse=True?
    We don't need to explicitly request this fixture in each test.
    pytest applies it automatically to all tests in this directory.

    This is the "guardrail" that ensures test isolation.
    Without it, one test's side effects would bleed into the next.
    """
    store.reset()
    yield
    # Teardown (after yield) — reset again to be safe
    store.reset()


@pytest.fixture
def sample_task(client):
    """
    Create a sample task and return its data.

    WHY a helper fixture?
    Many tests need an existing task (to test GET, PUT, DELETE).
    Instead of repeating the creation logic in every test, we centralise it.
    If the API changes, we fix it in ONE place, not in 15 test functions.
    """
    response = client.post(
        "/api/tasks",
        json={"title": "Sample Task", "description": "A fixture-created task"},
        content_type="application/json",
    )
    assert response.status_code == 201, "Fixture failed to create sample task"
    return response.get_json()["task"]
