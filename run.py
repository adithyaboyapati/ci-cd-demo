# run.py — Application Entry Point
# ==================================
#
# WHY A SEPARATE ENTRY POINT?
# In production (Docker/CI), we use gunicorn to run the app, not this file:
#   gunicorn "run:application" --bind 0.0.0.0:5000
#
# This file is for local development ONLY.
# The Dockerfile uses gunicorn directly for production-grade serving.
#
# HOW THE CD PIPELINE USES THIS:
# The pipeline doesn't call run.py at all. It builds a Docker image that
# uses the CMD ["gunicorn", "run:application"] instruction. This separates
# "how to develop" from "how to deploy."

from app import create_app

application = create_app("default")

if __name__ == "__main__":
    print("=" * 60)
    print("  CI/CD Demo App — Development Server")
    print("  Visit: http://localhost:5000/api/health")
    print("=" * 60)
    application.run(host="0.0.0.0", port=5000, debug=True)
