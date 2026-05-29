# =============================================================================
# Dockerfile — Multi-Stage Build
# =============================================================================
#
# WHY DOCKER IN CI/CD?
# Docker solves the "works on my machine" problem permanently.
# It packages your application + its exact runtime environment into a single
# artifact (an image) that runs identically everywhere:
#   - Developer's MacBook
#   - CI pipeline (Ubuntu runner)
#   - Production server (any cloud)
#
# WHY MULTI-STAGE?
# Stage 1 (builder): Installs ALL dependencies including build tools (~500MB)
# Stage 2 (runtime): Copies only what's needed to run the app (~80MB)
#
# Benefits:
#   - Smaller images → faster deployments → faster CD pipeline
#   - Smaller attack surface → fewer vulnerabilities flagged by security scan
#   - Build tools (gcc, pip) not present in production → more secure
#
# The CI pipeline builds this image and verifies it succeeds.
# The CD pipeline tags and pushes the verified image to a registry.
# =============================================================================

# =============================================================================
# STAGE 1: Builder
# Install dependencies in a temporary environment
# =============================================================================
FROM python:3.11-slim AS builder

# WHY --no-cache-dir?
# Don't store pip's download cache in the image — saves ~50MB per layer
# WHY WORKDIR /build?
# Isolates dependency installation from the app code
WORKDIR /build

# Copy ONLY the requirements file first.
# WHY? Docker caches layers. If we copy all code first, ANY code change
# would invalidate the dep installation cache — even if deps didn't change.
# This order ensures deps are only re-installed when requirements.txt changes.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# =============================================================================
# STAGE 2: Runtime
# Minimal image — only what's needed to run the application
# =============================================================================
FROM python:3.11-slim AS runtime

# Security best practice: never run as root inside a container.
# WHY: If the app is compromised, the attacker only has "appuser" permissions,
# not root permissions on the host. CI security scanners will flag root usage.
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed packages from builder stage (NOT the build tools)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy application code (everything except what's in .dockerignore)
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser run.py .

# Switch to non-root user before running anything
USER appuser

# Expose the port gunicorn will listen on
# WHY: This is documentation, not a firewall rule. The CD pipeline maps
# this port to a host port (or load balancer) during deployment.
EXPOSE 5000

# HEALTH CHECK — Docker's built-in mechanism for container health
# WHY: Docker Compose, Kubernetes, and AWS ECS use this to decide
# whether to route traffic to this container. If it fails, the old
# container keeps serving traffic until this one recovers.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')"

# Start the application with gunicorn (production WSGI server)
# WHY GUNICORN OVER flask run?
#   - Handles multiple concurrent requests (workers)
#   - Properly handles signals (graceful shutdown during CD deployments)
#   - Does NOT expose a debugger (flask run --debug is dangerous in production)
CMD ["gunicorn", "run:application", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
