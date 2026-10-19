#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
NODE_BIN="${NODE_BIN:-/Users/summerwindy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node}"
"$NODE_BIN" scripts/build-town-3d-capabilities.js
NODE_PATH="$PWD/design/river-park-3d-v1/node_modules" design/river-park-3d-v1/node_modules/.bin/esbuild design/town-ai-v9/src/viewer.js --bundle --format=iife --minify --outfile=design/town-ai-v9/viewer.bundle.js
python3 design/town-ai-v9/src/package_preview.py
