#!/usr/bin/env bash
# Build Flutter web app for deployment.
# Used by Cloudflare Pages (set as the Build Command in the dashboard),
# or run locally before pushing a pre-built frontend.
#
# Required env var (set in Cloudflare Pages dashboard):
#   API_BASE_URL  — public Railway backend URL, e.g. https://backend-xxxx.railway.app
#
# Usage (local):
#   API_BASE_URL=https://backend-xxxx.railway.app bash scripts/build-frontend.sh
set -euo pipefail

: "${API_BASE_URL:?'Error: API_BASE_URL is not set'}"

cd frontend
flutter pub get
flutter build web --dart-define=API_BASE_URL="${API_BASE_URL}"
echo "Build output: frontend/build/web"
