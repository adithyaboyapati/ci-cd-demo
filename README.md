# 🚀 CI/CD Pipeline Demo — Learn by Doing

A production-grade CI/CD pipeline demo built with Python/Flask + GitHub Actions + Docker.
Every file contains detailed comments explaining **why** each decision was made.

---

## 🧭 The Big Picture

```
Developer pushes code
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  GITHUB ACTIONS: CI Pipeline (ci.yml)                 │
│                                                       │
│  [Lint] → [Test + Coverage] → [Docker Build] → [Scan] │
│                                                       │
│  ✅ ALL PASS → PR can be merged                       │
│  ❌ ANY FAIL → PR is BLOCKED                         │
└───────────────────────────────────────────────────────┘
        │
        │ (merge to main)
        ▼
┌───────────────────────────────────────────────────────┐
│  GITHUB ACTIONS: CD Pipeline (cd.yml)                 │
│                                                       │
│  [Build Image] → [Push to GHCR] → [Create Release]   │
│                                                       │
│  Docker image tagged with commit SHA → immutable      │
│  GitHub Release auto-generated from commits           │
└───────────────────────────────────────────────────────┘
        │
        ▼
  ghcr.io/you/ci-cd-demo:latest  ← Pull and run anywhere
```

---

## 📁 Project Structure

```
ci_cd/
├── app/
│   ├── __init__.py       # Flask factory (why: testability + env config)
│   ├── config.py         # Environment configs (dev/test/prod)
│   ├── models.py         # Task data model + in-memory store
│   └── routes.py         # REST API endpoints + error handlers
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # pytest fixtures (test isolation)
│   └── test_api.py       # 25+ test cases (the CI gate)
│
├── .github/
│   └── workflows/
│       ├── ci.yml        # CI: lint → test → build → scan
│       └── cd.yml        # CD: publish → release → notify
│
├── Dockerfile            # Multi-stage build
├── docker-compose.yml    # Local dev environment
├── .dockerignore         # Keep images slim
├── .gitignore            # Never commit secrets or build artifacts
├── .flake8               # Linting rules
├── pyproject.toml        # pytest + coverage configuration
├── requirements.txt      # Production dependencies (pinned)
├── requirements-dev.txt  # Dev/CI dependencies
└── run.py                # App entry point
```

---

## ⚡ Quick Start (Local)

### Option A: Run with Python directly

```bash
# 1. Clone and enter the project
cd ci_cd

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install production dependencies
pip install -r requirements.txt

# 4. Run the app
python run.py
```

Visit: http://localhost:5000/api/health

### Option B: Run with Docker (recommended — same as production)

```bash
# Single command — zero setup required
docker compose up
```

Visit: http://localhost:5000/api/health

---

## 🧪 Run the Tests Locally

This is what the CI pipeline runs. Try it yourself before pushing:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run the full test suite (with coverage)
pytest

# Expected output:
# PASSED tests/test_api.py::TestHealthCheck::test_health_check_returns_200
# PASSED tests/test_api.py::TestCreateTask::test_create_task_with_valid_data_returns_201
# ... (25+ tests)
# Coverage: 85%+ ✅
```

### 💡 Learning Exercise: Break a Test Intentionally

```bash
# Edit app/routes.py — change line:
#   return jsonify({"status": "healthy", ...}), 200
# to:
#   return jsonify({"status": "ok", ...}), 200

# Now run tests:
pytest tests/test_api.py::TestHealthCheck

# You'll see:
# FAILED tests/test_api.py::TestHealthCheck::test_health_check_returns_healthy_status
# AssertionError: assert 'ok' == 'healthy'

# Push this to a branch and open a PR → CI will BLOCK the merge
# Fix it → CI passes → PR can merge
```

---

## 🔄 CI Pipeline Walkthrough

### How to trigger it:
1. Create a branch: `git checkout -b feature/my-change`
2. Make any change, commit, push
3. Go to **GitHub → Actions tab** → watch `🔄 Continuous Integration` run

### What each job does:

| Job | Tool | Why it exists |
|-----|------|---------------|
| 🔍 Lint | flake8 | Catch syntax/style errors before tests run |
| 🧪 Test & Coverage | pytest | Verify behavior; block if < 80% covered |
| 🐳 Build Docker | docker build | Verify Dockerfile compiles with current code |
| 🔒 Security Scan | Trivy | Find known CVEs in dependencies |
| ✅ CI Passed | bash | Single status check for branch protection |

### Reading CI failure output:

When a test fails, GitHub shows you exactly why:
```
FAILED tests/test_api.py::TestCreateTask::test_create_task_without_title_returns_400
AssertionError: assert 201 == 400
  (your code returned 201 when it should have returned 400)
```

No guessing. No "it works on my machine." The machine tells you what broke.

---

## 🚀 CD Pipeline Walkthrough

### How to trigger it:
Merge a PR to `main` (or push directly to `main`)

### What it does:

1. **Builds the Docker image** with multi-stage optimization
2. **Tags it with THREE tags:**
   - `sha-abc123def456` — exact commit (immutable, traceable)
   - `v1.0.42-abc123d` — human-readable version
   - `latest` — "give me the newest one"
3. **Pushes to GHCR** (GitHub Container Registry — free)
4. **Creates a GitHub Release** with auto-generated changelog
5. **Writes a deployment summary** in the Actions UI

### Pull and run the published image:

```bash
# After CD runs, anyone can pull and run your app:
docker pull ghcr.io/YOUR_GITHUB_USERNAME/ci_cd:latest
docker run -p 5000:5000 ghcr.io/YOUR_GITHUB_USERNAME/ci_cd:latest

# Verify it's running:
curl http://localhost:5000/api/health
# {"status": "healthy", "service": "ci-cd-demo-api", "tasks_count": 0}
```

---

## 📡 API Reference

Base URL: `http://localhost:5000/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (used by CD pipeline) |
| GET | `/tasks` | List all tasks |
| POST | `/tasks` | Create a task |
| GET | `/tasks/<id>` | Get one task |
| PUT | `/tasks/<id>` | Update a task |
| DELETE | `/tasks/<id>` | Delete a task |

### Example API calls:

```bash
# Health check
curl http://localhost:5000/api/health

# Create a task
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn CI/CD", "description": "Build a pipeline demo"}'

# List all tasks
curl http://localhost:5000/api/tasks

# Mark a task complete (use the id from the create response)
curl -X PUT http://localhost:5000/api/tasks/<id> \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

---

## 🎓 Step-by-Step Learning Path

### Step 1: Run tests, understand what we're protecting
```bash
pip install -r requirements-dev.txt
pytest -v
```
Read the test names. These are the CONTRACTS your code must fulfill.

### Step 2: Break a test, see CI catch it
Edit `app/routes.py` to introduce a bug. Push to a branch. Watch CI fail.

### Step 3: Fix it, see CI pass
Revert your change. Watch the green checkmarks appear.

### Step 4: Open a Pull Request
GitHub will show the CI status check on the PR.
You cannot merge until all checks pass.

### Step 5: Merge to main
Watch the CD pipeline trigger automatically.

### Step 6: Find your Docker image in GitHub Packages
Go to: `https://github.com/YOUR_USERNAME?tab=packages`
Pull and run the image that was just published.

### Step 7: Read the GitHub Release
Go to: `https://github.com/YOUR_USERNAME/ci_cd/releases`
See the auto-generated changelog from your commit messages.

---

## 🛡️ Setting Up Branch Protection (Critical for Teams)

To make the CI pipeline actually **enforce** the quality gate:

1. Go to **GitHub → Your Repo → Settings → Branches**
2. Click **Add branch protection rule**
3. Branch name pattern: `main`
4. Check: ✅ **Require status checks to pass before merging**
5. Add status check: `✅ CI Passed`
6. Check: ✅ **Require branches to be up to date before merging**
7. Save

Now no one — not even the repo owner — can merge code that fails CI.

---

## 🔑 GitHub Setup (Required for CD)

The CD pipeline pushes to GitHub Container Registry. It uses `GITHUB_TOKEN`
which is **automatically available** in every GitHub Actions run.

No additional secrets setup is required for GHCR!

For the `packages: write` permission, the `cd.yml` already includes:
```yaml
permissions:
  contents: write
  packages: write
```

---

## 🤔 Common Questions

**Q: Why not use `flask run` in Docker?**
`flask run` is a development server. It's single-threaded and exposes a
debugger. Gunicorn handles multiple concurrent requests and is production-safe.

**Q: Why pin exact package versions?**
`Flask>=3.0` could install Flask 3.1 next month, which might have breaking
changes. Pinned versions guarantee identical environments everywhere.

**Q: Why 80% coverage minimum?**
100% is unrealistic. 0% is useless. 80% is a practical threshold that catches
most bugs without demanding tests for every trivial getter. You can raise it
as the codebase matures.

**Q: Why separate CI and CD workflows?**
They have different triggers and different purposes. CI is informational — it
tells you if code is good. CD is consequential — it publishes artifacts. Keeping
them separate makes it easy to re-run just the CI without triggering a publish.

---

## 🧱 Extending This Demo

| Feature | What to add |
|---------|------------|
| Real database | Add PostgreSQL to docker-compose, use SQLAlchemy, add `services:` to CI |
| Staging environment | Add a second deploy job in cd.yml targeting a staging server |
| Slack notifications | Add `slackapi/slack-github-action` to the notify job |
| Auto-rollback | Add a `verify-deployment` job with `curl /health` after deploy |
| Dependency updates | Add Dependabot config (`.github/dependabot.yml`) |
