"""
Linguo SQLite WAL Persistence, Migrations & Starter Deck Seeding
Maintains the audit log, flashcards database, and canonical CEFR archetypes.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from .config import DB_PATH, LOG_PATH
from .starter_deck import STARTER_DECK, ARCHETYPES


def init_db(seed_cards: bool = True):
    """Initializes SQLite database with WAL mode, runs migrations, and seeds starter deck."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                original_text TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                corrected_english TEXT NOT NULL,
                grammar_tip TEXT,
                thai_script TEXT NOT NULL,
                thai_phonetic TEXT NOT NULL,
                thai_breakdown TEXT,
                audio_thai_path TEXT,
                audio_eng_path TEXT,
                english_level TEXT,
                english_better_alternative TEXT,
                pronunciation_tip TEXT,
                thai_grammar_tip TEXT,
                is_starred INTEGER DEFAULT 0,
                error_category TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_category TEXT NOT NULL,
                sprite_name TEXT NOT NULL,
                card_title TEXT NOT NULL,
                cefr_level TEXT DEFAULT 'B1',
                card_type TEXT NOT NULL,
                front_challenge TEXT NOT NULL,
                back_solution TEXT NOT NULL,
                british_council_rule TEXT NOT NULL,
                gag_quote TEXT,
                thai_script TEXT NOT NULL,
                thai_phonetic TEXT NOT NULL,
                thai_tones TEXT NOT NULL,
                thai_breakdown TEXT,
                source_history_ids TEXT,
                is_mastered INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS card_archetypes (
                category TEXT PRIMARY KEY,
                sprite_name TEXT NOT NULL,
                card_title TEXT NOT NULL,
                cefr_level TEXT DEFAULT 'B1',
                card_type TEXT NOT NULL,
                front_challenge TEXT NOT NULL,
                back_solution TEXT NOT NULL,
                british_council_rule TEXT NOT NULL,
                gag_quote TEXT,
                thai_script TEXT NOT NULL,
                thai_phonetic TEXT NOT NULL,
                thai_tones TEXT NOT NULL,
                thai_breakdown TEXT
            )
        """)

        # Schema migration: ensure any older tables gain new columns if missing
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(history)")
        columns = [row[1] for row in cursor.fetchall()]
        new_cols = {
            "english_level": "TEXT",
            "english_better_alternative": "TEXT",
            "pronunciation_tip": "TEXT",
            "thai_grammar_tip": "TEXT",
            "is_starred": "INTEGER DEFAULT 0",
            "error_category": "TEXT"
        }
        for col, col_type in new_cols.items():
            if col not in columns:
                try:
                    conn.execute(f"ALTER TABLE history ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

        # Seed archetypes and starter deck
        seed_archetypes_if_needed(conn)
        if seed_cards:
            seed_starter_deck_if_needed(conn)
        conn.commit()


def seed_archetypes_if_needed(conn: sqlite3.Connection = None):
    """Seeds default archetypes into SQLite card_archetypes table if missing."""
    def _seed(c):
        for cat, data in ARCHETYPES.items():
            c.execute("""
                INSERT OR IGNORE INTO card_archetypes (
                    category, sprite_name, card_title, cefr_level, card_type,
                    front_challenge, back_solution, british_council_rule, gag_quote,
                    thai_script, thai_phonetic, thai_tones, thai_breakdown
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cat, data["sprite"], data["title"], data["cefr"], data["type"],
                data["front_challenge"], data["back_solution"], data["rule"], data["gag"],
                data["thai_script"], data["thai_phonetic"], data["thai_tones"], data["thai_breakdown"]
            ))
        c.commit()

    if conn is not None:
        _seed(conn)
    else:
        with sqlite3.connect(DB_PATH) as c:
            _seed(c)


def seed_starter_deck_if_needed(conn: sqlite3.Connection = None):
    """Seeds any missing canonical CEFR A1-B2 starter deck cards into cards table."""
    def _seed(c):
        cursor = c.cursor()
        cursor.execute("SELECT error_category FROM cards;")
        existing_cats = {r[0] for r in cursor.fetchall()}
        for card in STARTER_DECK:
            if card["category"] not in existing_cats:
                cursor.execute("""
                    INSERT INTO cards (
                        error_category, sprite_name, card_title, cefr_level, card_type,
                        front_challenge, back_solution, british_council_rule, gag_quote,
                        thai_script, thai_phonetic, thai_tones, thai_breakdown,
                        source_history_ids, is_mastered
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 0)
                """, (
                    card["category"], card["sprite"], card["title"], card["cefr"], card["type"],
                    card["front_challenge"], card["back_solution"], card["rule"], card["gag"],
                    card["thai_script"], card["thai_phonetic"], card["thai_tones"], card["thai_breakdown"]
                ))
        c.commit()

    if conn is not None:
        _seed(conn)
    else:
        with sqlite3.connect(DB_PATH) as c:
            _seed(c)


def get_archetype(category: str) -> dict:
    """Dynamically loads archetype from SQLite table, falling back to Python defaults."""
    cat = category.upper().strip()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM card_archetypes WHERE category = ?", (cat,))
            row = cur.fetchone()
            if row:
                return {
                    "sprite": row["sprite_name"],
                    "title": row["card_title"],
                    "cefr": row["cefr_level"],
                    "type": row["card_type"],
                    "front_challenge": row["front_challenge"],
                    "back_solution": row["back_solution"],
                    "rule": row["british_council_rule"],
                    "gag": row["gag_quote"],
                    "thai_script": row["thai_script"],
                    "thai_phonetic": row["thai_phonetic"],
                    "thai_tones": row["thai_tones"],
                    "thai_breakdown": row["thai_breakdown"],
                }
    except Exception:
        pass
    return ARCHETYPES.get(cat, ARCHETYPES.get("VERB_PATTERNS"))


def save_record(data: dict, original_text: str, thai_audio: str = "", eng_audio: str = "") -> int:
    """Persists a coached session into SQLite history and human-readable Markdown log."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO history (
                original_text, is_correct, corrected_english, grammar_tip,
                thai_script, thai_phonetic, thai_breakdown, audio_thai_path, audio_eng_path,
                english_level, english_better_alternative, pronunciation_tip, thai_grammar_tip, is_starred, error_category
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """, (
            original_text,
            1 if data.get("is_correct") else 0,
            data.get("corrected_english", ""),
            data.get("grammar_tip", ""),
            data.get("thai_concise_script", ""),
            data.get("thai_phonetic_western", ""),
            data.get("thai_breakdown", ""),
            thai_audio,
            eng_audio,
            data.get("english_level", "B1"),
            data.get("english_better_alternative", ""),
            data.get("pronunciation_tip", ""),
            data.get("thai_grammar_tip", ""),
            data.get("error_category", "NONE")
        ))
        conn.commit()
        rec_id = cur.lastrowid

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_icon = "✅" if data.get("is_correct") else "⚠️"
    level = data.get("english_level", "B1")
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n### [{timestamp}] Entry #{rec_id} [{level}] {status_icon}\n")
            f.write(f"- **Input**: {original_text}\n")
            f.write(f"- **Corrected**: {data.get('corrected_english')}\n")
            f.write(f"- **Grammar Tip**: {data.get('grammar_tip')}\n")
            if data.get("english_better_alternative"):
                f.write(f"- **Level-Up Alternative**: {data.get('english_better_alternative')}\n")
            if data.get("pronunciation_tip"):
                f.write(f"- **Pronunciation & Phonetics**: {data.get('pronunciation_tip')}\n")
            f.write(f"- **Thai**: `{data.get('thai_concise_script')}` -> **`{data.get('thai_phonetic_western')}`**\n")
            f.write(f"- **Breakdown**: {data.get('thai_breakdown')}\n")
            if data.get("thai_grammar_tip"):
                f.write(f"- **Thai Grammar**: {data.get('thai_grammar_tip')}\n")
    except Exception:
        pass

    return rec_id


def toggle_star(record_id: int):
    """Toggles favorite status (★) on a history entry for focused memorization."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_starred FROM history WHERE id = ?", (record_id,))
        row = cur.fetchone()
        if not row:
            print(f"❌ Entry #{record_id} non trovata.")
            return
        new_val = 0 if row[0] else 1
        cur.execute("UPDATE history SET is_starred = ? WHERE id = ?", (new_val, record_id))
        conn.commit()
    star_icon = "★ Aggiunto ai preferiti" if new_val else "☆ Rimosso dai preferiti"
    print(f"✨ Entry #{record_id}: {star_icon}")
