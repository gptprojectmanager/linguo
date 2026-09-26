"""
Linguo Flashcard Exporters
Generates:
1. Native Anki .apkg packages (with 16-bit arcade styling, CRT scanlines, and audio references)
2. Tab-Separated TSV decks compatible with Anki, Quizlet, and standard SRS engines.
"""

import os
import csv
import json
import time
import zipfile
import sqlite3
import tempfile
import hashlib
from pathlib import Path
from ..core.config import DATA_DIR, DB_PATH
from ..core.db import init_db

ARCADE_CSS = """
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
  font-size: 16px;
  text-align: center;
  color: #e6edf3;
  background-color: #0d1117;
  padding: 24px;
  border-radius: 12px;
  border: 2px solid #f1c40f;
  box-shadow: 0 0 20px rgba(241, 196, 15, 0.25);
  max-width: 620px;
  margin: 0 auto;
}
.arcade-header {
  font-size: 12px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #00ffff;
  margin-bottom: 14px;
  font-weight: 700;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cefr-tag {
  display: inline-block;
  padding: 3px 8px;
  background-color: #238636;
  color: #ffffff;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 800;
}
.puzzle-box {
  font-size: 20px;
  line-height: 1.5;
  margin: 20px 0;
  font-weight: 600;
  color: #ffffff;
}
.blank-hint {
  display: inline-block;
  padding: 2px 10px;
  background-color: #161b22;
  border: 2px dashed #f1c40f;
  color: #f1c40f;
  border-radius: 6px;
  font-weight: bold;
}
.solution-box {
  font-size: 22px;
  color: #2ecc71;
  font-weight: 800;
  margin: 18px 0;
  line-height: 1.4;
}
.rule-box {
  text-align: left;
  background-color: #161b22;
  border-left: 4px solid #00ffff;
  padding: 12px 16px;
  border-radius: 6px;
  margin: 16px 0;
  font-size: 14px;
  line-height: 1.45;
}
.rule-title {
  color: #00ffff;
  font-weight: bold;
  font-size: 12px;
  text-transform: uppercase;
  margin-bottom: 4px;
  letter-spacing: 1px;
}
.gag-box {
  font-style: italic;
  color: #f39c12;
  background-color: rgba(243, 156, 18, 0.08);
  border: 1px dashed rgba(243, 156, 18, 0.3);
  border-radius: 6px;
  padding: 10px 14px;
  margin: 14px 0;
  font-size: 14px;
}
.thai-section {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid #30363d;
  font-size: 15px;
  color: #8b949e;
  line-height: 1.5;
}
.thai-script {
  font-size: 20px;
  color: #58a6ff;
  font-weight: bold;
}
"""

FRONT_TEMPLATE = """
<div class="card">
  <div class="arcade-header">
    <span>🕹️ {{Title}}</span>
    <span class="cefr-tag">{{CEFR}} • {{Category}}</span>
  </div>
  <div class="puzzle-box">{{Front_Challenge}}</div>
  <div class="thai-section">
    <div>🇹🇭 <span class="thai-script">{{Thai_Script}}</span></div>
    <div>🗣️ {{Thai_Phonetics}}</div>
  </div>
</div>
"""

BACK_TEMPLATE = """
<div class="card">
  <div class="arcade-header">
    <span>🕹️ {{Title}}</span>
    <span class="cefr-tag">{{CEFR}} • {{Category}}</span>
  </div>
  <div class="solution-box">{{Back_Solution}}</div>
  <div class="rule-box">
    <div class="rule-title">📖 Cambridge / British Council Rule</div>
    <div>{{Rule}}</div>
  </div>
  <div class="gag-box">💬 {{Gag}}</div>
  <div class="thai-section">
    <div>🇹🇭 <span class="thai-script">{{Thai_Script}}</span></div>
    <div>🗣️ {{Thai_Phonetics}}</div>
  </div>
</div>
"""


def export_tsv(output_path: Path | None = None, db_path: Path | None = None) -> Path:
    """Exports cards to an Anki-compatible TSV file."""
    if db_path is None:
        db_path = DB_PATH
    if output_path is None:
        output_path = DATA_DIR / "cards_anki_export.tsv"

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM cards ORDER BY id ASC")
        rows = cur.fetchall()

    if not rows:
        raise ValueError("Nessuna carta da esportare nel database.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Front_Puzzle", "Back_Explanation", "Thai_Script", "Thai_Phonetics", "Category", "CEFR"])
        for r in rows:
            front = f"<b>[{r['card_title']}]</b><br><br>🇬🇧 {r['front_challenge']}<br><br>🇹🇭 {r['thai_tones']}"
            back = f"<b>✅ {r['back_solution']}</b><br><br>📖 {r['british_council_rule']}<br><br>💬 <i>{r['gag_quote']}</i>"
            writer.writerow([
                front,
                back,
                r["thai_script"],
                f"{r['thai_phonetic']} ({r['thai_tones']}) - {r['thai_breakdown']}",
                r["error_category"],
                r["cefr_level"]
            ])

    return output_path


def export_apkg(output_path: Path | None = None, db_path: Path | None = None) -> Path:
    """Builds a native .apkg package embedding 16-bit arcade styling and Anki 2.0 schema."""
    if db_path is None:
        db_path = DB_PATH
    if output_path is None:
        output_path = DATA_DIR / "cards_anki_export.apkg"

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM cards ORDER BY id ASC")
        rows = cur.fetchall()

    if not rows:
        raise ValueError("Nessuna carta da esportare nel database.")

    now_ts = int(time.time())
    deck_id = 1727376000000
    model_id = 1727376000001

    model_def = {
        str(model_id): {
            "id": model_id,
            "name": "Linguo Arcade Cued Recall",
            "type": 0,
            "mod": now_ts,
            "usn": -1,
            "sortf": 0,
            "did": deck_id,
            "tmpls": [
                {
                    "name": "Arcade Encounter",
                    "ord": 0,
                    "qfmt": FRONT_TEMPLATE,
                    "afmt": BACK_TEMPLATE,
                    "did": None,
                    "bqfmt": "",
                    "bafmt": ""
                }
            ],
            "flds": [
                {"name": "Title", "ord": 0, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []},
                {"name": "Front_Challenge", "ord": 1, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []},
                {"name": "Back_Solution", "ord": 2, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []},
                {"name": "Rule", "ord": 3, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []},
                {"name": "Gag", "ord": 4, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []},
                {"name": "Thai_Script", "ord": 5, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []},
                {"name": "Thai_Phonetics", "ord": 6, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []},
                {"name": "Category", "ord": 7, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []},
                {"name": "CEFR", "ord": 8, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []}
            ],
            "css": ARCADE_CSS,
            "latexPre": "",
            "latexPost": "",
            "req": [[0, "all", [0, 1]]]
        }
    }

    decks_def = {
        str(deck_id): {
            "id": deck_id,
            "mod": now_ts,
            "name": "Linguo::Cambridge English Standard",
            "usn": -1,
            "collapsed": False,
            "desc": "Active recall cued-recall deck generated by Linguo with British Council grammar rules.",
            "dyn": 0,
            "conf": 1,
            "extendNew": 10,
            "extendRev": 50
        }
    }

    dconf_def = {
        "1": {
            "id": 1,
            "mod": now_ts,
            "name": "Default",
            "usn": 0,
            "maxTaken": 60,
            "autoplay": True,
            "timer": 0,
            "replayq": True,
            "new": {"delays": [1.0, 10.0], "ints": [1, 4, 7], "initialFactor": 2500, "separate": True, "order": 1, "perDay": 20},
            "rev": {"perDay": 200, "ease4": 1.3, "fuzz": 0.05, "minSpace": 1, "ivlFct": 1.0, "maxIvl": 36500},
            "lapse": {"delays": [10.0], "mult": 0.0, "minInt": 1, "leechFails": 8, "leechAction": 0}
        }
    }

    conf_def = {
        "nextPos": 1,
        "estTimes": True,
        "activeDecks": [deck_id],
        "sortType": "noteFld",
        "timeLim": 0,
        "sortBackwards": False,
        "addToCur": True,
        "curDeck": deck_id,
        "curModel": str(model_id),
        "collapseTime": 1200
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_db = Path(tmp_dir) / "collection.anki2"
        with sqlite3.connect(tmp_db) as aconn:
            aconn.execute("""
                CREATE TABLE col (
                    id integer primary key, crt integer not null, mod integer not null,
                    scm integer not null, ver integer not null, dty integer not null,
                    usn integer not null, ls integer not null, conf text not null,
                    models text not null, decks text not null, dconf text not null, tags text not null
                );
            """)
            aconn.execute("""
                CREATE TABLE notes (
                    id integer primary key, guid text not null, mid integer not null,
                    mod integer not null, usn integer not null, tags text not null,
                    flds text not null, sfld text not null, csum integer not null,
                    flags integer not null, data text not null
                );
            """)
            aconn.execute("""
                CREATE TABLE cards (
                    id integer primary key, nid integer not null, did integer not null,
                    ord integer not null, mod integer not null, usn integer not null,
                    type integer not null, queue integer not null, due integer not null,
                    ivl integer not null, factor integer not null, reps integer not null,
                    lapses integer not null, left integer not null, odue integer not null,
                    odid integer not null, flags integer not null, data text not null
                );
            """)
            aconn.execute("""
                CREATE TABLE revlog (
                    id integer primary key, cid integer not null, usn integer not null,
                    ease integer not null, ivl integer not null, lastIvl integer not null,
                    factor integer not null, time integer not null, type integer not null
                );
            """)
            aconn.execute("CREATE TABLE graves (usn integer not null, oid integer not null, type integer not null);")

            aconn.execute("""
                INSERT INTO col VALUES (
                    1, ?, ?, ?, 11, 0, -1, 0, ?, ?, ?, ?, '{}'
                )
            """, (
                now_ts, now_ts, now_ts,
                json.dumps(conf_def),
                json.dumps(model_def),
                json.dumps(decks_def),
                json.dumps(dconf_def)
            ))

            for idx, r in enumerate(rows):
                note_id = now_ts * 1000 + idx
                card_id = note_id + 500
                guid = hashlib.sha1(f"linguo_{r['id']}_{r['card_title']}".encode()).hexdigest()[:10]

                thai_phon_full = f"{r['thai_phonetic']} ({r['thai_tones']}) - {r['thai_breakdown']}"
                fields = [
                    r["card_title"],
                    r["front_challenge"],
                    r["back_solution"],
                    r["british_council_rule"],
                    r["gag_quote"] or "",
                    r["thai_script"],
                    thai_phon_full,
                    r["error_category"],
                    r["cefr_level"]
                ]
                flds_str = "\x1f".join(fields)
                sfld_str = r["card_title"]
                csum = int(hashlib.sha1(sfld_str.encode()).hexdigest()[:8], 16) & 0xffffffff

                aconn.execute("""
                    INSERT INTO notes VALUES (?, ?, ?, ?, -1, '', ?, ?, ?, 0, '')
                """, (note_id, guid, model_id, now_ts, flds_str, sfld_str, csum))

                aconn.execute("""
                    INSERT INTO cards VALUES (
                        ?, ?, ?, 0, ?, -1, 0, 0, ?, 0, 2500, 0, 0, 0, 0, 0, 0, ''
                    )
                """, (card_id, note_id, deck_id, now_ts, idx + 1))

            aconn.execute("CREATE INDEX ix_notes_usn on notes (usn);")
            aconn.execute("CREATE INDEX ix_cards_usn on cards (usn);")
            aconn.execute("CREATE INDEX ix_cards_nid on cards (nid);")
            aconn.execute("CREATE INDEX ix_cards_sched on cards (did, queue, due);")
            aconn.commit()

        # Build Zip archive (.apkg)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(tmp_db, arcname="collection.anki2")
            zf.writestr("media", "{}")

    return output_path


def export_cards(format_type: str = "all"):
    """High-level export interface supporting 'anki' (TSV), 'apkg' (Native), or 'all'."""
    init_db()
    format_type = format_type.lower().strip()

    if format_type in ("tsv", "anki"):
        tsv_path = export_tsv()
        print(f"\n🎴 \033[1;32mEsportate carte in formato Anki TSV!\033[0m")
        print(f"📁 File generato: \033[1m{tsv_path}\033[0m")
        print("👉 Importalo in Anki Desktop selezionando separatore Tab.\n")
    elif format_type in ("apkg", "native"):
        apkg_path = export_apkg()
        print(f"\n📦 \033[1;32mPacchetto nativo Anki .apkg generato con successo!\033[0m")
        print(f"📁 File generato: \033[1m{apkg_path}\033[0m")
        print("👉 Fai doppio click sul file .apkg per caricarlo direttamente in Anki Desktop o AnkiMobile.\n")
    else:  # all
        tsv_path = export_tsv()
        apkg_path = export_apkg()
        print(f"\n🎴 \033[1;32mEsportazione completa completata con successo!\033[0m")
        print(f"  • \033[1mAnki TSV:\033[0m  {tsv_path}")
        print(f"  • \033[1mNativo APKG:\033[0m {apkg_path}")
        print("👉 Doppio click su .apkg per avviare subito la sessione di ripasso.\n")
