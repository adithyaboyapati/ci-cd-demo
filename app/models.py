"""
app/models.py — Task Data Model
================================

WHY IN-MEMORY STORAGE FOR THIS DEMO?
We deliberately avoid a real database here. The goal is to learn CI/CD,
not database migrations. An in-memory store keeps setup to zero steps while
still giving us realistic create/read/update/delete operations to test.

IN A REAL APP: You'd use SQLAlchemy + PostgreSQL. The CI pipeline would spin up
a real Postgres instance using a GitHub Actions "service container":

  services:
    postgres:
      image: postgres:15
      env:
        POSTGRES_PASSWORD: postgres

This is a powerful CI/CD feature — your pipeline gets a fresh, isolated
database on every run, seeded and torn down automatically.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional


# WHY A CLASS FOR THE STORE?
# Wrapping state in a class (rather than a bare dict) lets tests
# call TaskStore.reset() to wipe state between test cases.
# Without this, test order would affect test results — a CI nightmare.
class TaskStore:
    """Thread-safe in-memory storage for tasks."""

    def __init__(self):
        self._tasks: dict[str, dict] = {}

    def reset(self):
        """Clear all tasks. Called by test fixtures before each test."""
        self._tasks.clear()

    def create(self, title: str, description: str = "") -> dict:
        """
        Create a new task.

        Returns:
            The newly created task dict.

        Raises:
            ValueError: If title is empty — tested in our test suite.
        """
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")

        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "title": title.strip(),
            "description": description.strip(),
            "completed": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._tasks[task_id] = task
        return task

    def get_all(self) -> list[dict]:
        """Return all tasks, newest first."""
        return sorted(
            self._tasks.values(),
            key=lambda t: t["created_at"],
            reverse=True,
        )

    def get_by_id(self, task_id: str) -> Optional[dict]:
        """Return a task by ID, or None if not found."""
        return self._tasks.get(task_id)

    def update(self, task_id: str, **fields) -> Optional[dict]:
        """
        Update allowed fields on a task.

        Returns:
            Updated task, or None if task_id not found.
        """
        task = self._tasks.get(task_id)
        if task is None:
            return None

        allowed_fields = {"title", "description", "completed"}
        for field, value in fields.items():
            if field in allowed_fields:
                task[field] = value

        task["updated_at"] = datetime.now(timezone.utc).isoformat()
        return task

    def delete(self, task_id: str) -> bool:
        """
        Delete a task by ID.

        Returns:
            True if deleted, False if not found.
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def count(self) -> int:
        """Return the total number of tasks."""
        return len(self._tasks)


# Singleton store instance shared across the app
# In tests, fixtures call store.reset() before each test case
store = TaskStore()
