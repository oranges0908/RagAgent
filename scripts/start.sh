#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

docker compose up -d

echo ""
echo "  App:      http://localhost"
echo "  Papers:   http://localhost/api/papers"
echo "  Upload:   POST http://localhost/api/upload"
echo "  Query:    POST http://localhost/api/query/stream"
echo ""
echo "  Logs:     bash scripts/logs.sh [backend|frontend]"
echo "  Status:   bash scripts/status.sh"
echo "  Stop:     bash scripts/stop.sh"
echo ""
