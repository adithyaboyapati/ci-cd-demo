"""
app/config.py — Environment Configuration
==========================================

WHY SEPARATE CONFIG CLASSES?
A core CI/CD principle is: "Build once, deploy many times."
Your Docker image is built ONCE in CI. That same image is then promoted through
environments (testing → staging → production). Config classes make this possible
by externalising all environment-specific values.

12-FACTOR APP PRINCIPLE #3: Config
  "Store config in the environment" — https://12factor.net/config
  Production secrets are NEVER in source code. They are injected as environment
  variables at runtime — by your CI/CD system, Kubernetes secrets, or a vault.
"""

import os


class BaseConfig:
    """
    Shared settings across ALL environments.
    These values are safe to commit because they are not secrets.
    """
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-not-for-production")
    JSON_SORT_KEYS = False  # Preserve insertion order in API responses
    TESTING = False
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    """
    Local development — verbose errors, debug mode on.
    NEVER use in production: debug mode exposes an interactive shell.
    """
    DEBUG = True


class TestingConfig(BaseConfig):
    """
    CI/CD test runs — predictable, isolated, no side effects.

    WHY TESTING = True?
    Flask disables error catching in test mode so exceptions propagate fully,
    giving us accurate failure messages in our CI logs.
    """
    TESTING = True
    DEBUG = True
    # Use a separate in-memory store for tests so each test suite starts clean
    # This is the key to making tests deterministic (same result every time)


class ProductionConfig(BaseConfig):
    """
    Production — hardened, no debug, secrets from environment variables.

    WHY os.environ.get() with no default?
    If SECRET_KEY is missing in production, the app CRASHES at startup rather
    than silently using an insecure key. Fail fast is a CI/CD best practice.
    """
    SECRET_KEY = os.environ.get("SECRET_KEY")  # No fallback — must be set!
    DEBUG = False
