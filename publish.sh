#!/usr/bin/env bash
# publish.sh - Automates data extraction and portfolio deployment

set -e

echo "Starting publish flow..."

# 1. Run the dev-knowledge extraction (Replace with actual command when implemented)
echo "Extracting knowledge (Simulated)..."
# e.g., python3 main.py -> generates output/*.json

# 2. Define paths
DEV_KNOWLEDGE_DIR=$(pwd)
# Assuming portfolio is a sibling directory based on your current setup
PORTFOLIO_DIR="../portfolio" 

if [ ! -d "$PORTFOLIO_DIR" ]; then
    echo "Error: Portfolio directory not found at $PORTFOLIO_DIR"
    exit 1
fi

# 3. Copy generated files to portfolio (Uncomment when generator is ready)
echo "Copying data to private portfolio repository..."
mkdir -p "$PORTFOLIO_DIR/data"
# cp -r output/*.json "$PORTFOLIO_DIR/data/"

# 4. Commit and push the portfolio repo
echo "Pushing portfolio to trigger Vercel..."
cd "$PORTFOLIO_DIR"

# Stage the data folder
git add data/

# Check if there are actually changes to commit
if git diff --cached --quiet; then
    echo "No new data changes detected. Skipping push."
else
    git commit -m "chore: auto-update dev-knowledge data"
    
    # Assuming 'main' is the default branch
    git push origin main
    
    echo "Successfully pushed data to portfolio. Vercel build triggered!"
fi

cd "$DEV_KNOWLEDGE_DIR"
echo "Publish complete!"
