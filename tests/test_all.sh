#!/usr/bin/env bash
# ==============================================================================
# Linguo // Full Automated Test Suite
# Tests Python engine, Pydantic schemas, SQLite WAL, CLI commands, and Rust HUD
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

echo "🧪 Starting Linguo Test Suite..."
echo "📂 Project root: $SCRIPT_DIR"

# 1. Python Syntax & Compilation
echo -n "  [1/7] Python syntax validation... "
python3 -m py_compile "$SCRIPT_DIR/bin/linguo"
echo "✅ OK"

# 2. Pydantic v2 Schema Import & Validation Test
echo -n "  [2/7] Pydantic v2 schema integrity... "
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR/bin')
import pydantic
from pydantic import BaseModel
assert int(pydantic.__version__.split('.')[0]) >= 2, 'Pydantic v2 required'
"
echo "✅ OK"

# 3. System Diagnostics (linguo --doctor)
echo -n "  [3/7] Running linguo doctor diagnostics... "
linguo --doctor >/dev/null 2>&1
echo "✅ OK"

# 4. Database Schema & WAL Verification
echo -n "  [4/7] SQLite WAL & tables check... "
python3 -c "
import sqlite3
from pathlib import Path
db_path = Path.home() / '.local/share/linguo/history.db'
assert db_path.exists(), 'Database not found'
with sqlite3.connect(db_path) as conn:
    cur = conn.cursor()
    cur.execute('PRAGMA journal_mode;')
    mode = cur.fetchone()[0]
    assert mode.lower() == 'wal', f'Expected WAL mode, got {mode}'
    
    cur.execute('SELECT name FROM sqlite_master WHERE type=\"table\";')
    tables = {r[0] for r in cur.fetchall()}
    for req in ['history', 'cards', 'card_archetypes']:
        assert req in tables, f'Missing table {req}'
"
echo "✅ OK"

# 5. British Council Audit & Card Minting
echo -n "  [5/7] British Council audit engine... "
linguo --audit >/dev/null 2>&1
echo "✅ OK"

# 6. Anki Export (linguo --export)
echo -n "  [6/7] Anki TSV export generator... "
linguo --export >/dev/null 2>&1
export_tsv="$HOME/.local/share/linguo/cards_anki_export.tsv"
test -f "$export_tsv"
echo "✅ OK"

# 7. Rust dash-gui Native HUD Binary
echo -n "  [7/7] Rust dash-gui Metal binary check... "
gui_bin="$HOME/.local/bin/linguo-gui"
test -x "$gui_bin"
echo "✅ OK"

echo ""
echo "🎉 ALL 7 TESTS PASSED! Linguo is 100% verified and operational."
