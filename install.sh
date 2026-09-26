#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Installing Linguo..."

# 1. Directories
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.local/share/linguo/audio"
mkdir -p "$HOME/.local/share/linguo/workspace/.agents/agents/linguo"
mkdir -p "$HOME/.local/share/linguo/workspace/.agents/agents/linguo-fast"
mkdir -p "$HOME/.gemini/config/agents/linguo"
mkdir -p "$HOME/.gemini/config/agents/linguo-fast"

# 2. CLI Executable
cp "$SCRIPT_DIR/bin/linguo" "$HOME/.local/bin/linguo"
chmod +x "$HOME/.local/bin/linguo"
echo "✅ Copied binary to ~/.local/bin/linguo"

# 3. Agent Prompts
cp "$SCRIPT_DIR/agents/linguo-fast/agent.md" "$HOME/.local/share/linguo/workspace/.agents/agents/linguo-fast/agent.md"
cp "$SCRIPT_DIR/agents/linguo/agent.md" "$HOME/.local/share/linguo/workspace/.agents/agents/linguo/agent.md"
cp "$SCRIPT_DIR/agents/linguo-fast/agent.md" "$HOME/.gemini/config/agents/linguo-fast/agent.md"
cp "$SCRIPT_DIR/agents/linguo/agent.md" "$HOME/.gemini/config/agents/linguo/agent.md"
echo "✅ Synchronized Antigravity agent definitions"

# 4. Config
if [ ! -f "$HOME/.local/share/linguo/config.json" ]; then
    cp "$SCRIPT_DIR/config/config.sample.json" "$HOME/.local/share/linguo/config.json"
    echo "✅ Created initial ~/.local/share/linguo/config.json"
fi

# 5. Dependencies via uv
if command -v uv >/dev/null 2>&1; then
    echo "📦 Checking Python packages with uv..."
    uv pip install pydantic torch 'numpy<2' soundfile kokoro edge-tts
else
    echo "⚠️ uv not found in PATH. Please install uv (https://github.com/astral-sh/uv)"
fi

# 6. Rust Immediate-Mode GUI (dash-gui)
export PATH="$HOME/.cargo/bin:$PATH"
if command -v cargo >/dev/null 2>&1; then
    echo "🦀 Rust toolchain detected. Compiling dash-gui HUD..."
    "$SCRIPT_DIR/install_gui.sh"
else
    echo "ℹ️ Cargo not found. To build the native Rust HUD, install Rust (curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh) and run ./install_gui.sh"
fi

# 7. macOS Menu Bar Agent (com.linguo.bar)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🎙️ Configuring macOS Menu Bar login item..."
    "$HOME/.local/bin/linguo" --install-bar || true
fi

echo ""
echo "🎉 Linguo is installed! Available commands:"
echo "   linguo 'your phrase'       # Instant Cambridge analysis & dual audio"
echo "   linguo --gui (or linguo-gui) # Native 16-bit MTG HUD (Metal / 60fps)"
echo "   linguo --audit             # British Council gap audit (Gate 3 Flash 3.8 High)"
echo "   linguo --cards             # Review active MTG recall puzzle cards"
echo "   linguo --status-bar        # Check macOS Menu Bar status"
echo "   linguo --install-bar       # Install/enable Menu Bar icon at macOS login"
echo "   linguo --board (or lb)     # Open ADHD Flashcard TUI Board (curses)"
echo "   linguo --export            # Export Anki-compatible TSV deck"
echo "   linguo --preseed           # Cache 75 survival Thai audio bricks"
echo "   linguo --doctor            # Verify all engines and system permissions"

