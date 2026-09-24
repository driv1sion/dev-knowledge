#!/usr/bin/env bash
# publish.sh - Automates data extraction and remote portfolio deployment
# Usage: ./publish.sh <TARGET_REPO_URL> <PORTFOLIO_REPO_URL>

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <TARGET_REPO_URL> <PORTFOLIO_REPO_URL>"
    echo "Example: $0 https://github.com/user/cool-app.git https://github.com/user/portfolio.git"
    exit 1
fi

TARGET_REPO_URL=$1
PORTFOLIO_REPO_URL=$2

# Extract project name from the URL
PROJECT_NAME=$(basename "$TARGET_REPO_URL" .git)
RANDOM_STR=$(head -c 4 /dev/urandom | xxd -p)
TARGET_TMP_DIR="/tmp/devknowledge-target-${PROJECT_NAME}-${RANDOM_STR}"
PORTFOLIO_TMP_DIR="/tmp/devknowledge-portfolio-${RANDOM_STR}"

echo "Starting remote publish flow for $PROJECT_NAME..."

# Cleanup function to run on exit
cleanup() {
    echo "Cleaning up temporary directories..."
    rm -rf "$TARGET_TMP_DIR"
    rm -rf "$PORTFOLIO_TMP_DIR"
}
trap cleanup EXIT

# 1. Clone Target Repository (Blobless Clone for speed/memory efficiency)
echo "Cloning target repository (Blobless clone)..."
git clone --filter=blob:none "$TARGET_REPO_URL" "$TARGET_TMP_DIR"

# 2. Run dev-knowledge extraction
echo "Extracting knowledge..."
DEV_KNOWLEDGE_DIR=$(pwd)
source "$DEV_KNOWLEDGE_DIR/venv/bin/activate"

# We must run analyze on the target directory
devknowledge analyze "$TARGET_TMP_DIR"
devknowledge publish "$TARGET_TMP_DIR"

# 3. Clone Portfolio Repository (Shallow Clone for speed/memory efficiency)
echo "Cloning portfolio repository (Shallow clone)..."
git clone --depth 1 "$PORTFOLIO_REPO_URL" "$PORTFOLIO_TMP_DIR"

# 4. Copy generated files to portfolio and update projects index
echo "Copying data to private portfolio repository and updating index..."
mkdir -p "$PORTFOLIO_TMP_DIR/data"
cp "$TARGET_TMP_DIR/knowledge_graph.json" "$PORTFOLIO_TMP_DIR/data/${PROJECT_NAME}_knowledge_graph.json"
devknowledge update-portfolio "$PORTFOLIO_TMP_DIR/data" "$PROJECT_NAME" "$TARGET_TMP_DIR/knowledge_graph.json"

# 5. Commit and push the portfolio repo
echo "Pushing portfolio to trigger remote deployment..."
cd "$PORTFOLIO_TMP_DIR"

# Stage the data folder
git add data/

# Check if there are actually changes to commit
if git diff --cached --quiet; then
    echo "No new data changes detected. Skipping push."
else
    git commit -m "chore: auto-update dev-knowledge data for $PROJECT_NAME"
    
    # Push to default branch (main/master)
    git push origin HEAD
    
    echo "Successfully pushed data to remote portfolio!"
fi

echo "Publish complete!"
