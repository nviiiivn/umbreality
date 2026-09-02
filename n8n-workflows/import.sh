#!/bin/bash
# Import n8n workflows into running n8n instance
# Usage: bash import.sh
# Requires: n8n running at http://localhost:5678

N8N_URL="${N8N_URL:-http://localhost:5678}"
DIR="$(dirname "$0")"

echo "Importing n8n workflows from $DIR"
echo "Target: $N8N_URL"
echo ""

for f in "$DIR"/*.json; do
  name=$(basename "$f" .json)
  echo "Importing: $name..."
  
  # Try with API key if set, otherwise try without
  if [ -n "$N8N_API_KEY" ]; then
    curl -s -X POST "$N8N_URL/rest/workflows" \
      -H "Content-Type: application/json" \
      -H "X-N8N-API-KEY: $N8N_API_KEY" \
      -d @"$f" | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'  OK: id={d.get(\"data\",{}).get(\"id\",\"?\")}')" 2>/dev/null
  else
    # Get cookie first
    echo "  Set N8N_API_KEY or import manually via n8n UI"
    echo "  File: $f"
  fi
  echo ""
done

echo "Done. Import manually by going to n8n UI → Workflows → Import"
