#!/usr/bin/env bash
# ==============================================================================
# Linguo // macOS Native .app & .dmg Packager
# Packages the 60fps Metal Rust HUD into a double-clickable Linguo.app & Linguo.dmg
# Designed for non-technical users (Zero Terminal Required)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"
APP_NAME="Linguo"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
VERSION=$(grep -m1 '^version =' "$SCRIPT_DIR/pyproject.toml" | cut -d'"' -f2)
DMG_PATH="$DIST_DIR/$APP_NAME-$VERSION.dmg"

export PATH="$HOME/.cargo/bin:$PATH"

echo "📦 Packaging Linguo for macOS (Non-Technical User Release)..."

# 1. Compile Release Binary
echo "🦀 Compiling release binary in gui/dash-gui..."
cargo build --release --manifest-path "$SCRIPT_DIR/gui/dash-gui/Cargo.toml"

# 2. Prepare .app Bundle Structure
rm -rf "$DIST_DIR"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# 3. Copy Executable
cp "$SCRIPT_DIR/gui/dash-gui/target/release/dash-gui" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
chmod +x "$APP_BUNDLE/Contents/MacOS/$APP_NAME"

# 4. Generate Info.plist
cat <<EOF > "$APP_BUNDLE/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleDisplayName</key>
    <string>Linguo</string>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.gptcompany.linguo</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSMicrophoneUsageDescription</key>
    <string>Linguo requires microphone access for voice dictation and English coaching.</string>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
</dict>
</plist>
EOF

# 5. Ad-hoc Codesigning
if command -v codesign &>/dev/null; then
    echo "🔏 Applying ad-hoc codesignature to $APP_NAME.app..."
    codesign -s - --force --deep "$APP_BUNDLE" 2>/dev/null || true
fi

# 6. Create Drag-and-Drop .dmg Installer via hdiutil
echo "💿 Generating macOS installer disk image ($DMG_PATH)..."
DMG_STAGING="$DIST_DIR/dmg_staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"
cp -R "$APP_BUNDLE" "$DMG_STAGING/"
ln -s /Applications "$DMG_STAGING/Applications"

hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_STAGING" -ov -format UDZO "$DMG_PATH" >/dev/null
rm -rf "$DMG_STAGING"

echo ""
echo "🎉 SUCCESS! macOS Release packaged:"
echo "   📱 Application Bundle : $APP_BUNDLE"
echo "   💿 Drag & Drop .dmg  : $DMG_PATH"
echo ""
echo "👉 Per la tua ragazza / utenti non-terminal:"
echo "   1. Fai doppio clic su $APP_NAME-0.3.0.dmg"
echo "   2. Trascina Linguo.app in /Applications"
echo "   3. Aprilo con doppio clic: la HUD arcade 16-bit si avvia istantaneamente!"
