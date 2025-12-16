#!/usr/bin/env bash

set -euo pipefail

# Build the project first
echo "Building project..."
npm run clean && npm run build

# Update manifest.json with version from package.json
echo "Updating manifest version..."
VERSION=$(node -p "require('./package.json').version")

# Validate VERSION is not empty
if [ -z "$VERSION" ]; then
  echo "Error: VERSION is empty"
  exit 1
fi

# Use | delimiter to handle versions with special characters like /
sed "s|{{VERSION}}|$VERSION|g" manifest.json > manifest.json.tmp
mv manifest.json.tmp manifest.json

# Verify required files exist
for file in manifest.json icon.png package.json README.md LICENSE; do
  if [ ! -f "$file" ]; then
    echo "Error: Required file $file not found"
    exit 1
  fi
done

# Remove devDependencies
echo "Removing devDependencies and types from node_modules..."
rm -rf node_modules
# We already built `dist/` above. During the pruned install (prod deps only),
# `npm` would run lifecycle scripts like `prepare`, which would try to rebuild
# without devDependencies (typescript/@types/etc) and can fail. We explicitly
# ignore scripts here because the MCPB package should ship the prebuilt `dist/`.
npm ci --omit=dev --ignore-scripts --audit false --fund false

find node_modules -name "*.ts" -type f -delete 2>/dev/null || true

# Create the MCPB package
echo "Creating MCPB package..."
rm -rf sde-mcp.mcpb
# --no-dir-entries: https://github.com/anthropics/mcpb/issues/18#issuecomment-3021467806
zip --recurse-paths --no-dir-entries \
  sde-mcp.mcpb \
  manifest.json \
  icon.png \
  dist/ \
  node_modules/ \
  package.json \
  README.md \
  LICENSE

# Restore the template version (use | delimiter instead of /)
echo "Restoring manifest template..."
sed "s|$VERSION|{{VERSION}}|g" manifest.json > manifest.json.tmp
mv manifest.json.tmp manifest.json

# Restore full node_modules
echo "Restoring node_modules..."
npm ci --audit false --fund false

echo
echo "MCPB package created: sde-mcp.mcpb ($(du -h sde-mcp.mcpb | cut -f1))"