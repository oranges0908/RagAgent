#!/usr/bin/env bash
# =============================================================================
# Railway first-time setup for RagAgent
#
# Prerequisites:
#   npm install -g @railway/cli   # install Railway CLI
#   railway login                 # authenticate
#
# Usage:
#   GEMINI_API_KEY=your_key bash scripts/railway-setup.sh
# =============================================================================
set -euo pipefail

: "${GEMINI_API_KEY:?'Error: GEMINI_API_KEY is not set. Run: export GEMINI_API_KEY=your_key'}"

echo "=== RagAgent Railway Setup ==="
echo ""

# --------------------------------------------------------------------------
# Step 1: Link to Railway project
# --------------------------------------------------------------------------
echo "[1/5] Linking to Railway project..."
echo "      (Select the project you created at railway.app)"
railway link
echo ""

# --------------------------------------------------------------------------
# Step 2: Create and configure Backend service
# --------------------------------------------------------------------------
echo "[2/5] Configuring Backend service..."
echo "      ACTION REQUIRED: In the Railway dashboard,"
echo "      create a service named 'backend' from this GitHub repo."
echo "      Set its Dockerfile path to: docker/Dockerfile.backend"
echo ""
read -rp "      Press Enter once the backend service exists in Railway..."

railway variables --set "GEMINI_API_KEY=${GEMINI_API_KEY}" --service backend
echo "      ✓ GEMINI_API_KEY set on backend service"

# Optional: add a Railway volume for persistence
echo ""
echo "      OPTIONAL: Add a persistent volume in Railway dashboard:"
echo "        Service: backend → Volumes → Mount path: /app/storage"
echo "        (Without this, uploaded papers are lost on redeploy)"
echo ""
read -rp "      Press Enter to continue..."

# --------------------------------------------------------------------------
# Step 3: Deploy Backend
# --------------------------------------------------------------------------
echo ""
echo "[3/5] Deploying backend..."
railway up --service backend --detach
echo "      ✓ Backend deployment triggered"

# --------------------------------------------------------------------------
# Step 4: Get Backend public URL
# --------------------------------------------------------------------------
echo ""
echo "[4/5] Fetching backend public URL..."
echo "      ACTION REQUIRED: In the Railway dashboard,"
echo "      add a public domain to the 'backend' service (Settings → Domains)."
echo ""
read -rp "      Paste the backend public URL (e.g. https://backend-xxxx.railway.app): " BACKEND_PUBLIC_URL
BACKEND_PUBLIC_URL="${BACKEND_PUBLIC_URL%/}"  # strip trailing slash

# --------------------------------------------------------------------------
# Step 5: Create and configure Frontend service
# --------------------------------------------------------------------------
echo ""
echo "[5/5] Configuring Frontend service..."
echo "      ACTION REQUIRED: In the Railway dashboard,"
echo "      create a service named 'frontend' from this GitHub repo."
echo "      Set its Dockerfile path to: docker/Dockerfile.frontend"
echo ""
read -rp "      Press Enter once the frontend service exists in Railway..."

railway variables --set "BACKEND_URL=${BACKEND_PUBLIC_URL}" --service frontend
echo "      ✓ BACKEND_URL=${BACKEND_PUBLIC_URL} set on frontend service"

echo ""
echo "[5/5] Deploying frontend..."
railway up --service frontend --detach
echo "      ✓ Frontend deployment triggered"

# --------------------------------------------------------------------------
echo ""
echo "=== Setup Complete ==="
echo ""
echo "  Backend:  ${BACKEND_PUBLIC_URL}"
echo "  Frontend: Add a public domain to the 'frontend' service in Railway dashboard"
echo ""
echo "  Tip: future deploys are automatic on git push (if Railway GitHub integration is enabled)"
echo "       or run:  railway up --service backend && railway up --service frontend"
