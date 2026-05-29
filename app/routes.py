"""
app/routes.py — REST API Routes
=================================

WHY A BLUEPRINT?
Flask Blueprints are like mini-apps you can plug in and out of the main app.
This matters for CI/CD because:

  1. You can mount this blueprint at a different prefix per environment:
     - Local dev:   /api/tasks
     - Tests:       /api/tasks
     - Production:  /v1/tasks  (versioning without rewriting logic)

  2. Other microservices could import and test this blueprint in isolation.

THE HEALTH CHECK ENDPOINT (/health)
This is NOT just a nice-to-have — it's a CI/CD requirement:

  - Load balancers use it to decide if the container is alive (liveness probe)
  - CD pipelines use it to verify deployment succeeded before routing traffic
  - Monitoring systems use it to alert on-call engineers when service is down

  Without a health check, your CD pipeline can't verify a deployment worked.
"""

from flask import Blueprint, jsonify, request
from app.models import store

tasks_bp = Blueprint("tasks", __name__)


# =============================================================================
# HEALTH CHECK — Required by any serious production deployment
# =============================================================================

@tasks_bp.route("/healthy", methods=["GET"])
def health_check():
    """
    Liveness probe endpoint.

    CI/CD use: The CD pipeline calls this after deploying to verify the
    container started correctly. If this returns non-200, the deploy is
    marked as failed and rolled back automatically.

    Response format follows the Health Check Response Format RFC:
    https://inadarei.github.io/rfc-health-check/
    """
    return jsonify({
        "status": "healthy",
        "service": "ci-cd-demo-api",
        "tasks_count": store.count(),
    }), 200


# =============================================================================
# TASK CRUD ENDPOINTS
# =============================================================================

@tasks_bp.route("/tasks", methods=["GET"])
def list_tasks():
    """
    GET /api/tasks
    Returns all tasks, newest first.
    """
    tasks = store.get_all()
    return jsonify({
        "tasks": tasks,
        "count": len(tasks),
    }), 200


@tasks_bp.route("/tasks", methods=["POST"])
def create_task():
    """
    POST /api/tasks
    Body: { "title": "...", "description": "..." }

    WHY STRICT VALIDATION HERE?
    The CI pipeline runs tests that intentionally send bad data to this endpoint.
    If we don't validate, the app crashes with a 500 instead of returning a clean
    400. Tests catch this. Without tests, this bug would reach production.
    """
    data = request.get_json(silent=True)

    # Validation — each condition is tested in test_api.py
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Field 'title' is required and cannot be empty"}), 400

    try:
        task = store.create(
            title=title,
            description=data.get("description", ""),
        )
        return jsonify({"task": task, "message": "Task created successfully"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@tasks_bp.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id: str):
    """
    GET /api/tasks/<task_id>
    Returns 404 if task not found — tested in test suite.
    """
    task = store.get_by_id(task_id)
    if task is None:
        return jsonify({"error": f"Task '{task_id}' not found"}), 404
    return jsonify({"task": task}), 200


@tasks_bp.route("/tasks/<task_id>", methods=["PUT"])
def update_task(task_id: str):
    """
    PUT /api/tasks/<task_id>
    Body: { "title": "...", "description": "...", "completed": true/false }
    Returns 404 if task not found.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    task = store.update(task_id, **data)
    if task is None:
        return jsonify({"error": f"Task '{task_id}' not found"}), 404

    return jsonify({"task": task, "message": "Task updated successfully"}), 200


@tasks_bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str):
    """
    DELETE /api/tasks/<task_id>
    Returns 404 if task not found.
    """
    deleted = store.delete(task_id)
    if not deleted:
        return jsonify({"error": f"Task '{task_id}' not found"}), 404

    return jsonify({"message": f"Task '{task_id}' deleted successfully"}), 200


# =============================================================================
# ERROR HANDLERS — Return JSON, not HTML error pages
# =============================================================================

@tasks_bp.app_errorhandler(404)
def not_found(error):
    """WHY: Default Flask 404 returns HTML. APIs must return JSON."""
    return jsonify({"error": "The requested resource was not found"}), 404


@tasks_bp.app_errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


@tasks_bp.app_errorhandler(500)
def internal_error(error):
    """
    WHY: Never expose raw Python tracebacks in API responses.
    The full traceback IS logged (visible in CI/CD logs) but the client
    only sees a safe, generic message.
    """
    return jsonify({"error": "An internal server error occurred"}), 500
