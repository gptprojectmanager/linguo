#!/usr/bin/env python3
"""
Unit test suite for Linguo Core Engine (bin/linguo).
Covers Pydantic v2 schema validation, Gate 2 content moderation, configuration management,
SQLite WAL persistence, archetype seeding, and remote dispatch resolution.
"""

import os
import json
import sqlite3
import tempfile
from pathlib import Path
import pytest

# Import linguo as module
import sys
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from bin import linguo


class TestGate2SafetyFilter:
    def test_sensitive_weapons_and_violence(self):
        assert linguo.detect_sensitive_content("Where can I buy a gun?") is True
        assert linguo.detect_sensitive_content("He planned to bomb the station") is True
        assert linguo.detect_sensitive_content("Someone was stabbed with a knife") is True

    def test_sensitive_narcotics(self):
        assert linguo.detect_sensitive_content("Looking for high quality cocaine") is True
        assert linguo.detect_sensitive_content("He was arrested during a drug deal") is True
        assert linguo.detect_sensitive_content("Fentanyl overdose report") is True

    def test_sensitive_nsfw(self):
        assert linguo.detect_sensitive_content("Watching explicit porn movies") is True
        assert linguo.detect_sensitive_content("She worked as an escort prostitute") is True

    def test_safe_content(self):
        assert linguo.detect_sensitive_content("I want to buy a ticket to Bangkok") is False
        assert linguo.detect_sensitive_content("Please merge the pull request") is False
        assert linguo.detect_sensitive_content("We went to the market yesterday") is False
        assert linguo.detect_sensitive_content("") is False


class TestPydanticSchemaSanitization:
    def test_auto_heal_categories(self):
        validator = linguo.LinguoAnalysis.sanitize_error_category
        assert validator("articles") == "ARTICLES"
        assert validator("PREP") == "PREPOSITIONS"
        assert validator("past tense issue") == "TENSES"
        assert validator("verb pattern") == "VERB_PATTERNS"
        assert validator("word order error") == "WORD_ORDER"
        assert validator("singular agreement") == "AGREEMENT"
        assert validator("collocation mismatch") == "COLLOCATIONS"
        assert validator("NSFW content") == "SENSITIVE_NO_CARD"
        assert validator("random hallucination") == "NONE"
        assert validator("") == "NONE"
        assert validator(None) == "NONE"

    def test_sanitize_is_correct(self):
        validator = linguo.LinguoAnalysis.sanitize_is_correct
        assert validator(True) is True
        assert validator(False) is False
        assert validator("true") is True
        assert validator("1") is True
        assert validator("false") is False
        assert validator("0") is False

    def test_parse_and_validate_markdown_json(self):
        raw = """```json
        {
            "transcribed_english": "I go to gym",
            "is_correct": false,
            "error_category": "ARTICLES",
            "english_level": "A2",
            "corrected_english": "I go to the gym",
            "grammar_tip": "Use 'the' before specific public places.",
            "thai_concise_script": "ฉันไปยิม",
            "thai_phonetic_western": "chǎn bpai yim"
        }
        ```"""
        result = linguo.parse_and_validate_analysis(raw, fallback_input="I go to gym")
        assert result["is_correct"] is False
        assert result["error_category"] == "ARTICLES"
        assert result["corrected_english"] == "I go to the gym"
        assert result["thai_concise_script"] == "ฉันไปยิม"

    def test_parse_and_validate_sensitive_override(self):
        raw = """{
            "transcribed_english": "I want to buy a gun",
            "is_correct": true,
            "error_category": "NONE",
            "corrected_english": "I want to buy a gun"
        }"""
        result = linguo.parse_and_validate_analysis(raw, fallback_input="I want to buy a gun")
        assert result["error_category"] == "SENSITIVE_NO_CARD"

    def test_parse_and_validate_corrupt_json(self):
        raw = "This is not json at all."
        result = linguo.parse_and_validate_analysis(raw, fallback_input="Hello world")
        assert result["transcribed_english"] == "Hello world"
        assert result["is_correct"] is False
        assert result["error_category"] == "NONE"


class TestConfigurationManager:
    def test_load_and_save_config(self, monkeypatch, tmp_path):
        cfg_file = tmp_path / "config.json"
        monkeypatch.setattr(linguo, "CONFIG_PATH", cfg_file)

        # 1. Loading non-existent file creates default
        cfg = linguo.load_config()
        assert cfg["model"] == "gemini-3.6-flash-low"
        assert cfg["card_model"] == "gemini-3.8-flash-high"
        assert cfg_file.exists()

        # 2. Modify and save
        cfg["model"] = "gemini-3.7-flash-medium"
        cfg["speed"] = 0.75
        linguo.save_config(cfg)

        reloaded = linguo.load_config()
        assert reloaded["model"] == "gemini-3.7-flash-medium"
        assert reloaded["speed"] == 0.75

    def test_corrupt_config_recovers_to_default(self, monkeypatch, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text("{corrupt json", encoding="utf-8")
        monkeypatch.setattr(linguo, "CONFIG_PATH", cfg_file)

        cfg = linguo.load_config()
        assert cfg["model"] == "gemini-3.6-flash-low"


class TestRemoteDispatchResolution:
    def test_local_mode_returns_none(self):
        assert linguo.resolve_remote_endpoint("local") is None

    def test_custom_remote_url_override(self, monkeypatch):
        monkeypatch.setenv("LINGUO_REMOTE_URL", "http://custom-host:8765")
        monkeypatch.setenv("LINGUO_API_TOKEN", "test-token-123")
        endpoint = linguo.resolve_remote_endpoint("auto")
        assert endpoint == ("http://custom-host:8765", "test-token-123")

    def test_dell_mode_fallback_subdomain(self, monkeypatch):
        monkeypatch.delenv("LINGUO_REMOTE_URL", raising=False)
        monkeypatch.setenv("LINGUO_API_TOKEN", "secret-token")
        endpoint = linguo.resolve_remote_endpoint("dell")
        assert endpoint is not None
        assert endpoint[0].startswith("http")
        assert endpoint[1] == "secret-token"


class TestDatabaseAndArchetypes:
    def test_db_wal_and_schema(self, monkeypatch, tmp_path):
        db_file = tmp_path / "test_history.db"
        monkeypatch.setattr(linguo, "DB_PATH", db_file)

        linguo.init_db()
        assert db_file.exists()

        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode;")
            mode = cur.fetchone()[0]
            assert mode.lower() == "wal"

            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {r[0] for r in cur.fetchall()}
            assert "history" in tables
            assert "cards" in tables
            assert "card_archetypes" in tables

    def test_archetype_fallback(self):
        arch = linguo.get_archetype("ARTICLES")
        assert arch["title"] == "THE MARKET STAMP"
        assert arch["sprite"] == "the_stamp"

        arch_unknown = linguo.get_archetype("NON_EXISTENT_CAT")
        assert arch_unknown["title"] == "THE 'TO' TOLL"

    def test_classify_error(self):
        assert linguo.classify_error({"error_category": "ARTICLES"}) == "ARTICLES"
        assert linguo.classify_error({"error_category": "SENSITIVE_NO_CARD"}) == "SENSITIVE_NO_CARD"
        assert linguo.classify_error({"original_text": "I go to market"}) == "ARTICLES"
        assert linguo.classify_error({"original_text": "I went yesterday"}) == "TENSES"

    def test_record_persistence_and_starring(self, monkeypatch, tmp_path):
        db_file = tmp_path / "test_history.db"
        monkeypatch.setattr(linguo, "DB_PATH", db_file)
        linguo.init_db()

        sample_data = {
            "transcribed_english": "I goes to school",
            "is_correct": False,
            "corrected_english": "I go to school",
            "grammar_tip": "Use base form 'go' with 'I'.",
            "thai_concise_script": "ฉันไปโรงเรียน",
            "thai_phonetic_western": "chǎn bpai roong-rian",
            "thai_breakdown": "ฉัน = io | ไป = andare | โรงเรียน = scuola",
            "english_level": "A1",
            "english_better_alternative": "I attend school",
            "pronunciation_tip": "",
            "thai_grammar_tip": "",
            "error_category": "AGREEMENT"
        }

        rec_id = linguo.save_record(sample_data, original_text="I goes to school")
        assert rec_id > 0

        # Toggle star
        linguo.toggle_star(rec_id)
        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute("SELECT is_starred FROM history WHERE id = ?", (rec_id,))
            row = cur.fetchone()
            assert row[0] == 1


class TestConfigCliInteractions:
    def test_show_config_cli_options(self, monkeypatch, tmp_path, capsys):
        cfg_file = tmp_path / "config.json"
        monkeypatch.setattr(linguo, "CONFIG_PATH", cfg_file)

        # 1. Print matrix
        linguo.show_config_cli([])
        out = capsys.readouterr().out
        assert "Linguo Configuration Matrix" in out

        # 2. Update model
        linguo.show_config_cli(["model", "balanced"])
        cfg = linguo.load_config()
        assert cfg["model"] == "gemini-3.7-flash-medium"

        # 3. Update card model
        linguo.show_config_cli(["card", "canon"])
        cfg = linguo.load_config()
        assert cfg["card_model"] == "canon"

        # 4. Update tts
        linguo.show_config_cli(["tts", "local"])
        cfg = linguo.load_config()
        assert cfg["tts_engine"] == "local"

        # 5. Update speed
        linguo.show_config_cli(["speed", "0.75"])
        cfg = linguo.load_config()
        assert cfg["speed"] == 0.75

        # 6. Update voice
        linguo.show_config_cli(["voice", "adam"])
        cfg = linguo.load_config()
        assert cfg["eng_voice"] == "am_adam"

        # 7. Update route
        linguo.show_config_cli(["route", "dell"])
        cfg = linguo.load_config()
        assert cfg["dispatch_mode"] == "dell"

        # 8. Reset
        linguo.show_config_cli(["reset"])
        cfg = linguo.load_config()
        assert cfg["model"] == "gemini-3.6-flash-low"


class TestTelemetryAndTracing:
    def test_perf_tracker(self):
        tracker = linguo.PerfTracker("unit_test_action")
        with tracker.measure("step_1"):
            import time
            time.sleep(0.01)
        timings = tracker.finish()
        assert "step_1" in timings
        assert timings["step_1"] >= 5.0  # ms

    def test_log_event_ndjson(self, monkeypatch, tmp_path):
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(linguo, "LOGS_DIR", logs_dir)

        linguo.log_event("INFO", "TEST_COMP", "Test message", {"key": "val"})
        jsonl = logs_dir / "linguo_events.jsonl"
        assert jsonl.exists()
        line = jsonl.read_text(encoding="utf-8").strip()
        data = json.loads(line)
        assert data["level"] == "INFO"
        assert data["component"] == "TEST_COMP"
        assert data["message"] == "Test message"
        assert data["meta"]["key"] == "val"


class TestExportSystem:
    def test_export_cards_anki(self, monkeypatch, tmp_path):
        db_file = tmp_path / "test_history.db"
        monkeypatch.setattr(linguo, "DB_PATH", db_file)
        linguo.init_db()

        # Seed card
        with sqlite3.connect(db_file) as conn:
            conn.execute("""
                INSERT INTO cards (
                    error_category, sprite_name, card_title, cefr_level, card_type,
                    front_challenge, back_solution, british_council_rule, gag_quote,
                    thai_script, thai_phonetic, thai_tones, thai_breakdown
                ) VALUES (
                    'ARTICLES', 'the_stamp', 'THE MARKET STAMP', 'B1', 'Encounter',
                    'I go to [ ? ] market', 'I go to THE market', 'Rule 1', 'Gag 1',
                    'ไปตลาด', 'bpai dtà-làat', 'M / L', 'breakdown'
                )
            """)

        monkeypatch.setattr(linguo, "DATA_DIR", tmp_path)
        export_path = tmp_path / "cards_anki_export.tsv"

        linguo.export_cards("anki")
        assert export_path.exists()
        content = export_path.read_text(encoding="utf-8")
        assert "Front_Puzzle" in content
        assert "THE MARKET STAMP" in content

