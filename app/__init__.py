"""
app/__init__.py — Flask Application Factory
============================================

WHY AN APPLICATION FACTORY?
Instead of creating the Flask app as a global object, we use a factory function
(create_app). This pattern has two major CI/CD benefits:

  1. TESTABILITY: Tests can call create_app("testing") to get a fresh, isolated
     app instance with test-safe settings (no real DB, predictable state).
     Without this, tests would share global state and produce flaky results.

  2. CONFIGURABILITY: CI, staging, and production can each pass a different
     config class. The same codebase behaves correctly in every environment.
"""

from flask import Flask
from app.routes import tasks_bp


def create_app(config_name: str = "default") -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: One of 'default', 'testing', or 'production'.
                     CI pipelines pass 'testing' to get isolated test behavior.

    Returns:
        A configured Flask application instance.
    """
    app = Flask(__name__)

    # --- Configuration by environment ---
    # WHY: The same Docker image runs in CI, staging, and production.
    # Configuration (not code) is what differs between environments.
    config_map = {
        "default": "app.config.DevelopmentConfig",
        "testing": "app.config.TestingConfig",
        "production": "app.config.ProductionConfig",
    }
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    # --- Register blueprints (feature modules) ---
    # WHY: Blueprints allow us to break the app into isolated modules.
    # Each module can be tested independently, which keeps our test suite fast.
    app.register_blueprint(tasks_bp, url_prefix="/api")

    return app
