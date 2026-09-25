#!/usr/bin/env bash
# ==============================================================================
# Linguo // 16-bit MTG HUD Installer
# Compiles dash-gui (Rust immediate-mode HUD) and installs to ~/.local/bin/linguo-gui
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.cargo/bin:$PATH"

if ! command -v cargo &>/dev/null; then
    echo "❌ Cargo/Rust non trovato in ~/.cargo/bin. Assicurati che Rust sia installato."
    exit 1
fi

echo "🦀 Compilazione release di dash-gui (Rust + Metal/eframe)..."
cargo build --release --manifest-path "$SCRIPT_DIR/gui/dash-gui/Cargo.toml"

BIN_SRC="$SCRIPT_DIR/gui/dash-gui/target/release/dash-gui"
BIN_DEST="$HOME/.local/bin/linguo-gui"

mkdir -p "$HOME/.local/bin"
cp "$BIN_SRC" "$BIN_DEST"
chmod +x "$BIN_DEST"

# Ad-hoc codesign on macOS to prevent Gatekeeper security warnings
if command -v codesign &>/dev/null; then
    codesign -s - --force "$BIN_DEST" 2>/dev/null || true
fi

echo "✅ dash-gui installato con successo in: $BIN_DEST"
echo "🕹️ Avvia la GUI con: linguo-gui (oppure: linguo --gui)"
