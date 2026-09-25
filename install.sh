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
    uv pip install torch 'numpy<2' soundfile kokoro edge-tts
else
    echo "⚠️ uv not found in PATH. Please install uv (https://github.com/astral-sh/uv)"
fi

echo ""
echo "🎉 Linguo is installed! Use:"
echo "   linguo 'your phrase'       # Analyze & synthesize"
echo "   linguo replay (or lr)      # Replay last"
echo "   linguo loop 3 (or ll)      # Loop 3x"
echo "   linguo board  (or lb)      # Open ADHD Flashcard TUI Board"
echo "   linguo star <id>           # Star / Favorite entry"
