# Banking Microservices (Python) Context

## Overview
This directory contains standard Python-based microservices (e.g., `auth-service`, `account-service`, etc.). They are designed to run in Docker containers using Uvicorn and share common logic from the `/common` directory.

## Build & CI/CD Pipeline
- **Pipeline Structure:** Managed by `Jenkinsfile` referencing the `standardPipeline.groovy` shared library.
- **Build Process:** Uses Kaniko inside Kubernetes to build the image.
  - **Important:** The Kaniko build context is the root of the `banking-source` repository, NOT the service folder itself, so it can include the `common/` directory.
  - Command: `/kaniko/executor --context \`pwd\` --dockerfile services/<service-name>/Dockerfile ...`
- **Registry:** Pushes images to `harbor.local/banking-demo/`.
- **GitOps CD:** After building, the pipeline automatically updates the `tag` field in `banking-gitops/apps/<service-name>/helm/values-dev.yaml` and pushes it to Git to trigger ArgoCD.

## Dependencies & Secrets
- Python dependencies are managed in `common/requirements.txt`.
- Database/Redis credentials must not be hardcoded. They are injected via `ExternalSecret` into the Pod environment variables (refer to `banking-gitops/apps/<service-name>/helm/values-<env>.yaml`).
