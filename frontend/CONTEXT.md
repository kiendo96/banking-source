# Banking Frontend (React) Context

## Overview
This is a standard React SPA (Single Page Application) using TailwindCSS for styling.

## Build & Deployment
- **Dependencies:** Managed via npm (`package.json`).
- **Styling:** Uses PostCSS and Tailwind. Ensure `tailwind.config.js` paths cover all necessary UI components.
- **CI/CD:** Like backend services, it uses a Jenkins pipeline to build a Docker image (likely served by an Nginx container) and pushes it to Harbor.

## Configuration
- Any backend API URLs should be passed via environment variables during the build or injected dynamically at runtime via a config.js file served by Nginx. Do not hardcode `http://localhost` for production.
