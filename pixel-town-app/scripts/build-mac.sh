#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ELECTRON="$ROOT/../node_modules/electron/dist/Electron.app"
if [ ! -d "$ELECTRON" ]; then ELECTRON="$ROOT/node_modules/electron/dist/Electron.app"; fi
OUTPUT="$ROOT/dist-mac"
APP="$OUTPUT/像素小镇.app"
if [ -e "$APP" ]; then mv "$APP" "$OUTPUT/像素小镇-previous-$(date +%Y%m%d-%H%M%S).app"; fi
mkdir -p "$OUTPUT"
cp -R "$ELECTRON" "$APP"
RES="$APP/Contents/Resources"
mkdir -p "$RES/app/node_modules"
cp "$ROOT/package.json" "$RES/app/"
cp "$ROOT/README.md" "$RES/app/"
cp -R "$ROOT/main" "$ROOT/renderer" "$ROOT/assets" "$RES/app/"
if [ -d "$ROOT/shared" ]; then cp -R "$ROOT/shared" "$RES/app/"; fi
UNDICI="$ROOT/../node_modules/undici"
if [ ! -d "$UNDICI" ]; then UNDICI="$ROOT/node_modules/undici"; fi
cp -R "$UNDICI" "$RES/app/node_modules/undici"
mv "$APP/Contents/MacOS/Electron" "$APP/Contents/MacOS/像素小镇"
PLIST="$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Set :CFBundleName 像素小镇' "$PLIST"
/usr/libexec/PlistBuddy -c 'Set :CFBundleDisplayName 像素小镇' "$PLIST"
/usr/libexec/PlistBuddy -c 'Set :CFBundleIdentifier com.summerwindy.pixel-town-life' "$PLIST"
/usr/libexec/PlistBuddy -c 'Set :CFBundleExecutable 像素小镇' "$PLIST"
VERSION="$(node -p "require(process.argv[1]).version" "$ROOT/package.json")"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$PLIST"
if [ -f "$ROOT/build/town.icns" ]; then cp "$ROOT/build/town.icns" "$RES/town.icns"; /usr/libexec/PlistBuddy -c 'Set :CFBundleIconFile town.icns' "$PLIST"; fi
codesign --force --deep --sign - "$APP"
echo "独立安装包：$APP"
