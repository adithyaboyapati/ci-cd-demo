"""
tests/test_api.py — Full API Test Suite
=========================================

THESE TESTS ARE THE HEART OF YOUR CI PIPELINE.
The CI pipeline has one job: refuse to merge code that breaks these tests.

ANATOMY OF A GOOD CI TEST:
  1. FAST     — runs in milliseconds, not seconds. Fast tests = fast feedback.
  2. ISOLATED — does not depend on other tests, external services, or order.
  3. READABLE — when it fails, the engineer knows EXACTLY what broke.
  4. COMPLETE — covers both happy paths AND failure paths.

WHY TEST FAILURE PATHS?
Most bugs live in the paths "nobody expected":
  - "What if someone sends an empty title?"
  - "What if they delete a task that doesn't exist?"
  - "What if the JSON body is malformed?"

If you don't test these, your CI pipeline has blind spots.

COVERAGE GOAL: 80%
Our CI pipeline enforces 80% code coverage minimum (configured in pyproject.toml).
This means at least 80% of lines in app/ must be executed by this test suite.
If a new feature is added without tests, the pipeline blocks the merge.
"""

import pytest


# =============================================================================
# HEALTH CHECK TESTS
# =============================================================================

class TestHealthCheck:
    """
    WHY TEST THE HEALTH CHECK?
    The CD pipeline calls /api/health after deploying. If this endpoint
    is accidentally broken by a change, deployment verification fails
    and the pipeline auto-rolls back. Tests catch this BEFORE deployment.
    """

    def test_health_check_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self, client):
        data = response = client.get("/api/health").get_json()
        assert data["status"] == "healthy"

    def test_health_check_includes_service_name(self, client):
        data = client.get("/api/health").get_json()
        assert "service" in data
        assert data["service"] == "ci-cd-demo-api"

    def test_health_check_includes_task_count(self, client):
        data = client.get("/api/health").get_json()
        assert "tasks_count" in data
        assert isinstance(data["tasks_count"], int)


# =============================================================================
# CREATE TASK TESTS
# =============================================================================

class TestCreateTask:
    """Tests for POST /api/tasks"""

    def test_create_task_with_valid_data_returns_201(self, client):
        """Happy path — the most basic test."""
        response = client.post(
            "/api/tasks",
            json={"title": "Learn CI/CD"},
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_create_task_returns_task_with_id(self, client):
        """Verify the response contains a usable task ID."""
        response = client.post(
            "/api/tasks",
            json={"title": "Learn CI/CD"},
            content_type="application/json",
        )
        data = response.get_json()
        assert "task" in data
        assert "id" in data["task"]
        assert data["task"]["id"] is not None

    def test_create_task_stores_correct_title(self, client):
        """Data integrity — what goes in must come out unchanged."""
        response = client.post(
            "/api/tasks",
            json={"title": "My specific task title"},
            content_type="application/json",
        )
        data = response.get_json()
        assert data["task"]["title"] == "My specific task title"

    def test_create_task_with_description(self, client):
        response = client.post(
            "/api/tasks",
            json={"title": "Task with desc", "description": "Detailed description"},
            content_type="application/json",
        )
        data = response.get_json()
        assert data["task"]["description"] == "Detailed description"

    def test_create_task_defaults_to_not_completed(self, client):
        """New tasks should always start as incomplete."""
        response = client.post(
            "/api/tasks",
            json={"title": "New task"},
            content_type="application/json",
        )
        data = response.get_json()
        assert data["task"]["completed"] is False

    # --- FAILURE PATH TESTS (The ones that actually catch bugs) ---

    def test_create_task_without_title_returns_400(self, client):
        """
        WHY THIS TEST EXISTS:
        If the API doesn't validate, a task with no title gets created.
        That's a silent data corruption bug. This test makes it impossible
        to ship that bug — the CI pipeline would block the merge.
        """
        response = client.post(
            "/api/tasks",
            json={"description": "No title provided"},
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_create_task_with_empty_title_returns_400(self, client):
        response = client.post(
            "/api/tasks",
            json={"title": ""},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_task_with_whitespace_title_returns_400(self, client):
        """Edge case: "   " should be treated the same as an empty string."""
        response = client.post(
            "/api/tasks",
            json={"title": "   "},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_task_with_no_json_body_returns_400(self, client):
        """Malformed request — API must not crash with 500."""
        response = client.post(
            "/api/tasks",
            data="this is not json",
            content_type="text/plain",
        )
        assert response.status_code == 400


# =============================================================================
# LIST TASKS TESTS
# =============================================================================

class TestListTasks:
    """Tests for GET /api/tasks"""

    def test_list_tasks_returns_200(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200

    def test_list_tasks_empty_when_no_tasks(self, client):
        """
        WHY: Verifies the reset_store fixture works correctly.
        If this fails, our fixtures are broken → all other tests are unreliable.
        """
        data = client.get("/api/tasks").get_json()
        assert data["tasks"] == []
        assert data["count"] == 0

    def test_list_tasks_returns_created_tasks(self, client, sample_task):
        """After creating a task, it should appear in the list."""
        data = client.get("/api/tasks").get_json()
        assert data["count"] == 1
        assert data["tasks"][0]["id"] == sample_task["id"]

    def test_list_tasks_count_matches_tasks_length(self, client):
        """Data consistency — count field must always match actual array length."""
        # Create 3 tasks
        for i in range(3):
            client.post("/api/tasks", json={"title": f"Task {i}"})

        data = client.get("/api/tasks").get_json()
        assert data["count"] == len(data["tasks"])
        assert data["count"] == 3


# =============================================================================
# GET SINGLE TASK TESTS
# =============================================================================

class TestGetTask:
    """Tests for GET /api/tasks/<id>"""

    def test_get_task_returns_200_for_existing_task(self, client, sample_task):
        response = client.get(f"/api/tasks/{sample_task['id']}")
        assert response.status_code == 200

    def test_get_task_returns_correct_task(self, client, sample_task):
        data = client.get(f"/api/tasks/{sample_task['id']}").get_json()
        assert data["task"]["id"] == sample_task["id"]
        assert data["task"]["title"] == sample_task["title"]

    def test_get_task_returns_404_for_nonexistent_id(self, client):
        """
        WHY THIS MATTERS IN CI/CD:
        404 vs 500 is the difference between "expected case handled" and
        "the app crashed." CI catches crashes before they reach production.
        """
        response = client.get("/api/tasks/nonexistent-id-12345")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


# =============================================================================
# UPDATE TASK TESTS
# =============================================================================

class TestUpdateTask:
    """Tests for PUT /api/tasks/<id>"""

    def test_update_task_returns_200(self, client, sample_task):
        response = client.put(
            f"/api/tasks/{sample_task['id']}",
            json={"title": "Updated title"},
        )
        assert response.status_code == 200

    def test_update_task_changes_title(self, client, sample_task):
        client.put(
            f"/api/tasks/{sample_task['id']}",
            json={"title": "New title after update"},
        )
        data = client.get(f"/api/tasks/{sample_task['id']}").get_json()
        assert data["task"]["title"] == "New title after update"

    def test_update_task_can_mark_completed(self, client, sample_task):
        client.put(
            f"/api/tasks/{sample_task['id']}",
            json={"completed": True},
        )
        data = client.get(f"/api/tasks/{sample_task['id']}").get_json()
        assert data["task"]["completed"] is True

    def test_update_nonexistent_task_returns_404(self, client):
        response = client.put(
            "/api/tasks/does-not-exist",
            json={"title": "Update ghost task"},
        )
        assert response.status_code == 404

    def test_update_task_with_no_json_returns_400(self, client, sample_task):
        response = client.put(
            f"/api/tasks/{sample_task['id']}",
            data="bad data",
            content_type="text/plain",
        )
        assert response.status_code == 400


# =============================================================================
# DELETE TASK TESTS
# =============================================================================

class TestDeleteTask:
    """Tests for DELETE /api/tasks/<id>"""

    def test_delete_task_returns_200(self, client, sample_task):
        response = client.delete(f"/api/tasks/{sample_task['id']}")
        assert response.status_code == 200

    def test_deleted_task_no_longer_exists(self, client, sample_task):
        """Verify deletion is permanent — the task must be gone."""
        client.delete(f"/api/tasks/{sample_task['id']}")
        response = client.get(f"/api/tasks/{sample_task['id']}")
        assert response.status_code == 404

    def test_deleted_task_removed_from_list(self, client, sample_task):
        client.delete(f"/api/tasks/{sample_task['id']}")
        data = client.get("/api/tasks").get_json()
        assert data["count"] == 0

    def test_delete_nonexistent_task_returns_404(self, client):
        response = client.delete("/api/tasks/ghost-task-id")
        assert response.status_code == 404
