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

BUILD_UNIVERSAL=false
if [[ "${1:-}" == "--universal" ]] || [[ "${CI:-}" == "true" ]] || [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    BUILD_UNIVERSAL=true
fi

echo "📦 Packaging Linguo for macOS (Non-Technical User Release)..."

# 1. Compile Binary (Universal 2 or Host Native)
rm -rf "$DIST_DIR"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources/audio"

if [ "$BUILD_UNIVERSAL" = true ]; then
    echo "🦀 Building Universal 2 Binary (x86_64 Intel + aarch64 Apple Silicon)..."
    rustup target add x86_64-apple-darwin aarch64-apple-darwin 2>/dev/null || true
    cargo build --release --target x86_64-apple-darwin --manifest-path "$SCRIPT_DIR/gui/dash-gui/Cargo.toml"
    cargo build --release --target aarch64-apple-darwin --manifest-path "$SCRIPT_DIR/gui/dash-gui/Cargo.toml"
    lipo -create -output "$APP_BUNDLE/Contents/MacOS/$APP_NAME" \
        "$SCRIPT_DIR/gui/dash-gui/target/x86_64-apple-darwin/release/dash-gui" \
        "$SCRIPT_DIR/gui/dash-gui/target/aarch64-apple-darwin/release/dash-gui"
else
    echo "🦀 Compiling host native release binary in gui/dash-gui..."
    cargo build --release --manifest-path "$SCRIPT_DIR/gui/dash-gui/Cargo.toml"
    cp "$SCRIPT_DIR/gui/dash-gui/target/release/dash-gui" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
fi
chmod +x "$APP_BUNDLE/Contents/MacOS/$APP_NAME"

# 2. Bundle Offline Neural Audio Files for 15 Starter Cards
if [ -d "$HOME/.local/share/linguo/audio" ]; then
    echo "🎵 Bundling offline neural audio for 15 starter deck cards..."
    cp "$HOME/.local/share/linguo/audio"/eng_card_*.mp3 "$APP_BUNDLE/Contents/Resources/audio/" 2>/dev/null || true
    cp "$HOME/.local/share/linguo/audio"/thai_card_*.mp3 "$APP_BUNDLE/Contents/Resources/audio/" 2>/dev/null || true
fi

# 3. Generate Info.plist
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

# 4. Ad-hoc Codesigning
if command -v codesign &>/dev/null; then
    echo "🔏 Applying ad-hoc codesignature to $APP_NAME.app..."
    codesign -s - --force --deep "$APP_BUNDLE" 2>/dev/null || true
fi

# 5. Create Drag-and-Drop .dmg Installer via hdiutil with Helper Scripts
echo "💿 Generating macOS installer disk image ($DMG_PATH)..."
DMG_STAGING="$DIST_DIR/dmg_staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"
cp -R "$APP_BUNDLE" "$DMG_STAGING/"
ln -s /Applications "$DMG_STAGING/Applications"

# Add 1-Click Installer script for non-technical users (clears Gatekeeper quarantine automatically)
cat << 'EOF' > "$DMG_STAGING/Installa_Linguo.command"
#!/bin/bash
clear
echo "======================================================"
echo "   🎮 LINGUO // Installazione Automatica per macOS    "
echo "======================================================"
echo ""
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "📦 1. Installazione di Linguo in /Applications..."
rm -rf /Applications/Linguo.app
cp -R "$DIR/Linguo.app" /Applications/

echo "🔓 2. Sblocco autorizzazioni di sicurezza Gatekeeper..."
find /Applications/Linguo.app -exec xattr -c {} + 2>/dev/null || true

echo ""
echo "🎉 INSTALLAZIONE COMPLETATA CON SUCCESSO!"
echo "🚀 Avvio di Linguo in corso..."
sleep 1
open /Applications/Linguo.app

echo ""
echo "Puoi chiudere questa finestra del Terminale."
exit 0
EOF
chmod +x "$DMG_STAGING/Installa_Linguo.command"

# Add friendly instructions file
cat << 'EOF' > "$DMG_STAGING/LEGGIMI_PRIMA.txt"
======================================================
  🎮 LINGUO // BENVENUTA! GUIDA DI INSTALLAZIONE
======================================================

Hai 2 modi semplicissimi per installare Linguo:

METODO 1 (IL PIÙ VELOCE - UN SOLO CLIC):
  • Fai doppio clic sul file "Installa_Linguo.command".
  • Fa tutto lui in automatico: installa l'app in Applicazioni,
    sblocca i permessi e avvia Linguo istantaneamente!

METODO 2 (TRASCINA E RILASCIA):
  1. Trascina l'icona "Linguo" nella cartella "Applications".
  2. SOLO PER LA PRIMA VOLTA che apri l'app:
     - Vai nella cartella Applicazioni del tuo Mac.
     - Fai clic con il TASTO DESTRO del mouse (o due dita sul trackpad) su Linguo.
     - Clicca su "Apri" dal menu.
     - Nella finestrella di avviso, clicca sul pulsante "Apri".
  3. Dalle volte successive basterà un normale doppio clic!

Buono studio con Linguo! 🚀
======================================================
EOF

rm -f "$DMG_PATH"
hdiutil makehybrid -o "$DMG_PATH" "$DMG_STAGING" -hfs >/dev/null
rm -rf "$DMG_STAGING"

echo ""
echo "🎉 SUCCESS! macOS Release packaged:"
echo "   📱 Application Bundle : $APP_BUNDLE"
echo "   💿 Drag & Drop .dmg  : $DMG_PATH"
echo ""
echo "👉 Per la tua ragazza / utenti non-terminal:"
echo "   1. Fai doppio clic su $(basename "$DMG_PATH")"
echo "   2. Fai doppio clic su 'Installa_Linguo.command' oppure trascina Linguo in Applicazioni"
echo "   3. L'applicazione si avvia all'istante con 15 carte e audio neurale!"
