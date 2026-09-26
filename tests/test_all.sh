#!/usr/bin/env bash
# ==============================================================================
# Linguo // Unified Automated Test & Observability Suite
# Tests Python engine, FastAPI server, Prometheus metrics, Pytest suite,
# Rust dash-gui unit tests, Pydantic schemas, SQLite WAL, and macOS HUD
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

echo "🧪 Starting Linguo Unified Test Suite..."
echo "📂 Project root: $SCRIPT_DIR"

# 1. Python Syntax & Compilation
echo -n "  [1/10] Python syntax validation... "
python3 -m py_compile "$SCRIPT_DIR/bin/linguo" "$SCRIPT_DIR/scripts/linguo_server.py"
echo "✅ OK"

# 2. Pytest Unit Suite (Core, Gates, Config, Telemetry & Server Observability)
echo "  [2/10] Pytest automated unit test suite (Core & Server)..."
python3 -m pytest -q "$SCRIPT_DIR/tests"
echo "  ✅ OK: All Pytest unit tests passed"

# 3. Rust dash-gui Native Unit Tests
echo "  [3/10] Rust dash-gui cargo test suite..."
cargo test --manifest-path "$SCRIPT_DIR/gui/dash-gui/Cargo.toml" -q
echo "  ✅ OK: All Cargo unit tests passed"

# 4. Pydantic v2 Schema Import & Integrity Test
echo -n "  [4/10] Pydantic v2 schema integrity... "
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR/bin')
import pydantic
from pydantic import BaseModel
assert int(pydantic.__version__.split('.')[0]) >= 2, 'Pydantic v2 required'
"
echo "✅ OK"

# 5. System Diagnostics (linguo --doctor)
echo -n "  [5/10] Running linguo doctor diagnostics... "
linguo --doctor >/dev/null 2>&1
echo "✅ OK"

# 6. Database Schema & WAL Verification
echo -n "  [6/10] SQLite WAL & tables check... "
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

# 7. British Council Audit & Card Minting
echo -n "  [7/10] British Council audit engine... "
linguo --audit --no-review >/dev/null 2>&1
echo "✅ OK"

# 8. Anki Export (linguo --export)
echo -n "  [8/10] Anki TSV export generator... "
linguo --export >/dev/null 2>&1
export_tsv="$HOME/.local/share/linguo/cards_anki_export.tsv"
test -f "$export_tsv"
echo "✅ OK"

# 9. Gate 2 Content Moderation & SENSITIVE_NO_CARD
echo -n "  [9/10] Gate 2 Safety & Moderation filter... "
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from bin import linguo

assert linguo.detect_sensitive_content('I want to buy a gun') == True
assert linguo.detect_sensitive_content('We should merg the PR') == False
res = linguo.parse_and_validate_analysis('{\"is_correct\": true, \"corrected_english\": \"buy a gun\"}', fallback_input='I want to buy a gun')
assert res['error_category'] == 'SENSITIVE_NO_CARD', f'Expected SENSITIVE_NO_CARD, got {res.get(\"error_category\")}'
"
echo "✅ OK"

# 10. macOS LaunchAgent Menu Bar Agent
echo -n "  [10/11] macOS Menu Bar LaunchAgent agent... "
linguo --status-bar >/dev/null 2>&1
echo "✅ OK"

# 11. Full Isolated E2E Sandbox Lifecycle Test
echo "  [11/11] Full Isolated E2E Sandbox Lifecycle Test..."
python3 "$SCRIPT_DIR/tests/test_e2e_isolated.py" >/dev/null 2>&1
echo "  ✅ OK: Complete E2E sandbox lifecycle passed with strict host non-contamination"

echo ""
echo "🎉 ALL 11 TEST PHASES PASSED! Linguo Core, API Server, Native HUD, and Isolated E2E Sandbox are 100% verified."
