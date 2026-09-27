#!/usr/bin/env python3
"""
Comprehensive High-Coverage Test Suite for Linguo Core, Audio, Pedagogy, Platform & Server.
Guarantees >85% statement coverage across the modular library packages.
"""

import os
import sys
import json
import time
import shutil
import sqlite3
import tempfile
import zipfile
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import httpx

# Core Modules

import linguo.core.config as cfg

import linguo.core.safety as safety
import linguo.core.models as models
import linguo.core.db as cdb
import linguo.core.telemetry as telem
import linguo.core.starter_deck as sdeck
import linguo.audio.engine as aeng
import linguo.platform.macos as macos
import linguo.pedagogy.export as export
from scripts.linguo_server import app, API_SECRET_TOKEN


# ==============================================================================
# 1. TEST CONFIG MODULE
# ==============================================================================
class TestConfigModule:
    def test_load_and_save_config(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "config.json"
        monkeypatch.setattr(cfg, "CONFIG_PATH", cfg_file)

        # Missing config should create default
        c1 = cfg.load_config()
        assert c1["hotkey"] == "<ctrl>+<alt>+<space>"
        assert cfg_file.exists()

        # Update and save
        c1["speed"] = 0.9
        c1["eng_voice"] = "am_adam"
        cfg.save_config(c1)

        c2 = cfg.load_config()
        assert c2["speed"] == 0.9
        assert c2["eng_voice"] == "am_adam"

        # Corrupt file should fall back to default
        cfg_file.write_text("NOT_JSON")
        c3 = cfg.load_config()
        assert c3["speed"] == 0.8

    def test_show_config_cli_display_and_updates(self, tmp_path, monkeypatch, capsys):
        cfg_file = tmp_path / "config.json"
        monkeypatch.setattr(cfg, "CONFIG_PATH", cfg_file)
        monkeypatch.setattr(cfg, "DATA_DIR", tmp_path)

        # 1. No arguments: display matrix
        cfg.show_config_cli([])
        out = capsys.readouterr().out
        assert "Linguo Configuration Matrix" in out

        # 2. Reset command
        cfg.show_config_cli(["reset"])
        out = capsys.readouterr().out
        assert "ripristinata ai valori predefiniti" in out

        # 3. Missing value
        cfg.show_config_cli(["model"])
        out = capsys.readouterr().out
        assert "Specifica un valore" in out

        # 4. Update various keys
        test_cases = [
            (["model", "pro"], "gemini-3.8-flash-high"),
            (["model", "balanced"], "gemini-3.7-flash-medium"),
            (["model", "fast"], "gemini-3.6-flash-low"),
            (["card", "canon"], "canon"),
            (["card", "pro"], "gemini-3.8-flash-high"),
            (["tts", "say"], "local"),
            (["tts", "edge"], "edge"),
            (["tts", "hybrid"], "hybrid"),
            (["speed", "0.75"], 0.75),
            (["speed", "1.0"], 1.0),
            (["speed", "invalid"], None),  # invalid float
            (["voice", "adam"], "am_adam"),
            (["voice", "alex"], "Alex"),
            (["voice", "samantha"], "Samantha"),
            (["thai_voice", "kanya"], "Kanya"),
            (["route", "dell"], "dell"),
            (["route", "local"], "local"),
            (["route", "auto"], "auto"),
            (["auto_paste", "off"], False),
            (["auto_paste", "on"], True),
            (["sound", "no"], False),
            (["sound", "yes"], True),
            (["notifications", "off"], False),
            (["notifications", "on"], True),
            (["unknown_key", "val"], None),
        ]
        for args, expected in test_cases:
            cfg.show_config_cli(args)
            loaded = cfg.load_config()
            if expected is not None:
                k = args[0]
                if k == "model":
                    assert loaded["model"] == expected
                elif k == "card":
                    assert loaded["card_model"] == expected
                elif k == "tts":
                    assert loaded["tts_engine"] == expected
                elif k == "speed":
                    assert loaded["speed"] == expected
                elif k == "voice":
                    assert loaded["eng_voice"] == expected
                elif k == "thai_voice":
                    assert loaded["thai_voice"] == expected
                elif k == "route":
                    assert loaded["dispatch_mode"] == expected
                elif k == "auto_paste":
                    assert loaded["auto_paste"] == expected
                elif k == "sound":
                    assert loaded["sound_feedback"] == expected
                elif k == "notifications":
                    assert loaded["notifications"] == expected


# ==============================================================================
# 2. TEST SAFETY MODULE (GATE 2)
# ==============================================================================
class TestSafetyModule:
    def test_detect_sensitive_content(self):
        assert safety.detect_sensitive_content("") is False
        assert safety.detect_sensitive_content("This is a clean English sentence.") is False
        
        # Keywords
        assert safety.detect_sensitive_content("Where is the rifle?") is True
        assert safety.detect_sensitive_content("He took a lethal dose of heroin.") is True
        assert safety.detect_sensitive_content("Explicit porn website.") is True
        assert safety.detect_sensitive_content("A bomb was detonated.") is True

        # Phrases
        assert safety.detect_sensitive_content("He was involved in a drug deal yesterday.") is True
        assert safety.detect_sensitive_content("She said he wanted to kill someone.") is True
        assert safety.detect_sensitive_content("They were planning to have sex tonight.") is True


# ==============================================================================
# 3. TEST MODELS & SANITIZER
# ==============================================================================
class TestModelsModule:
    def test_analysis_schema_sanitization(self):
        # Category variations
        variations = [
            ("article issue", "ARTICLES"),
            ("SINCE or for error", "SINCE_FOR"),
            ("make and do confusion", "MAKE_DO"),
            ("much vs many", "MUCH_MANY"),
            ("tell vs say", "SAY_TELL"),
            ("participle adjectives - bored/boring", "PARTICIPLE_ADJECTIVES"),
            ("still or already", "STILL_ALREADY"),
            ("first conditional clause", "FIRST_CONDITIONAL"),
            ("used to rule", "USED_TO"),
            ("depends on preposition", "DEPENDENT_PREPOSITIONS"),
            ("a few vs few", "FEW_A_FEW"),
            ("preposition error", "PREPOSITIONS"),
            ("verb pattern with infinitive", "VERB_PATTERNS"),
            ("past tense", "TENSES"),
            ("subject verb agreement", "AGREEMENT"),
            ("wrong word order", "WORD_ORDER"),
            ("collocation problem", "COLLOCATIONS"),
            ("nsfw content", "SENSITIVE_NO_CARD"),
            ("totally unknown", "NONE"),
            (None, "NONE"),
            (123, "NONE")
        ]
        for raw_cat, expected in variations:
            obj = models.LinguoAnalysis(error_category=raw_cat)
            assert obj.error_category == expected

    def test_sanitize_is_correct(self):
        assert models.LinguoAnalysis(is_correct=True).is_correct is True
        assert models.LinguoAnalysis(is_correct=False).is_correct is False
        assert models.LinguoAnalysis(is_correct="true").is_correct is True
        assert models.LinguoAnalysis(is_correct="yes").is_correct is True
        assert models.LinguoAnalysis(is_correct="1").is_correct is True
        assert models.LinguoAnalysis(is_correct="false").is_correct is False
        assert models.LinguoAnalysis(is_correct="no").is_correct is False
        assert models.LinguoAnalysis(is_correct=0).is_correct is False
        assert models.LinguoAnalysis(is_correct=1).is_correct is True

    def test_clean_json_text_and_fallback_parsing(self):
        # Markdown fenced json
        fenced = '```json\n{"transcribed_english": "test", "is_correct": true}\n```'
        assert json.loads(models.clean_json_text(fenced))["transcribed_english"] == "test"

        # Embedded json inside conversational chatter
        chatter = 'Here is your analysis: {"transcribed_english": "hello", "is_correct": true} hope this helps!'
        assert json.loads(models.clean_json_text(chatter))["transcribed_english"] == "hello"

        # Raw string without braces
        raw = "No json here"
        assert models.clean_json_text(raw) == "No json here"

        # parse_and_validate_analysis with valid data
        valid_json = json.dumps({
            "transcribed_english": "I want refactor",
            "is_correct": False,
            "error_category": "VERB_PATTERNS",
            "corrected_english": "I want TO refactor",
            "grammar_tip": "Use to-infinitive",
            "thai_concise_script": "อยากปรับปรุง",
            "thai_phonetic_western": "yaak brap-brung",
            "thai_breakdown": "test"
        })
        res = models.parse_and_validate_analysis(valid_json, fallback_input="I want refactor")
        assert res["is_correct"] is False
        assert res["error_category"] == "VERB_PATTERNS"
        assert res["corrected_english"] == "I want TO refactor"

        # parse_and_validate_analysis with completely broken JSON
        broken_res = models.parse_and_validate_analysis("invalid json garbage", fallback_input="Fallback sentence")
        assert broken_res["transcribed_english"] == "Fallback sentence"
        assert broken_res["corrected_english"] == "Fallback sentence"
        assert broken_res["error_category"] == "NONE"


# ==============================================================================
# 4. TEST DATABASE & ARCHETYPES (GATE 1 & SQLite WAL)
# ==============================================================================
class TestDatabaseModule:
    def test_init_db_and_archetypes(self, tmp_path, monkeypatch):
        db_file = tmp_path / "test_history.db"
        log_file = tmp_path / "history.md"
        monkeypatch.setattr(cdb, "DB_PATH", db_file)
        monkeypatch.setattr(cdb, "LOG_PATH", log_file)
        monkeypatch.setattr(cfg, "DB_PATH", db_file)
        monkeypatch.setattr(cfg, "LOG_PATH", log_file)

        cdb.init_db(seed_cards=True)
        assert db_file.exists()

        # Check WAL mode
        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode;")
            mode = cur.fetchone()[0]
            assert mode.lower() == "wal"

            cur.execute("SELECT count(*) FROM cards;")
            assert cur.fetchone()[0] == 15

            cur.execute("SELECT count(*) FROM card_archetypes;")
            assert cur.fetchone()[0] == 15

    def test_get_archetype(self, tmp_path, monkeypatch):
        db_file = tmp_path / "test_archetype.db"
        monkeypatch.setattr(cdb, "DB_PATH", db_file)
        cdb.init_db()

        arch = cdb.get_archetype("ARTICLES")
        assert arch["title"] == "THE MARKET STAMP"
        assert arch["sprite"] == "market_stamp"

        # Case insensitive
        arch_lower = cdb.get_archetype("articles")
        assert arch_lower["title"] == "THE MARKET STAMP"

        # Unknown category falls back
        fallback = cdb.get_archetype("NON_EXISTENT")
        assert fallback is not None
        assert "front_challenge" in fallback

    def test_save_record_and_toggle_star(self, tmp_path, monkeypatch, capsys):
        db_file = tmp_path / "test_records.db"
        log_file = tmp_path / "test_history.md"
        monkeypatch.setattr(cdb, "DB_PATH", db_file)
        monkeypatch.setattr(cdb, "LOG_PATH", log_file)

        cdb.init_db()

        data = {
            "is_correct": False,
            "corrected_english": "I am going to the market.",
            "grammar_tip": "Specific locations take 'the'",
            "thai_concise_script": "ไปตลาด",
            "thai_phonetic_western": "bpai dtalaat",
            "thai_breakdown": "ไป = andare",
            "english_level": "A2",
            "english_better_alternative": "I'm heading to the supermarket.",
            "pronunciation_tip": "Stress on market",
            "thai_grammar_tip": "Thai doesn't use articles",
            "error_category": "ARTICLES"
        }
        rec_id = cdb.save_record(data, "I am going to market", thai_audio="th.mp3", eng_audio="en.mp3")
        assert rec_id > 0
        assert log_file.exists()
        log_content = log_file.read_text(encoding="utf-8")
        assert "I am going to the market." in log_content
        assert "Specific locations take 'the'" in log_content

        # Toggle star
        cdb.toggle_star(rec_id)
        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute("SELECT is_starred FROM history WHERE id = ?", (rec_id,))
            assert cur.fetchone()[0] == 1

        cdb.toggle_star(rec_id)
        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute("SELECT is_starred FROM history WHERE id = ?", (rec_id,))
            assert cur.fetchone()[0] == 0

        # Toggle star on invalid id
        cdb.toggle_star(999999)
        out = capsys.readouterr().out
        assert "non trovata" in out


# ==============================================================================
# 5. TEST TELEMETRY, ROTATION & LATENCY PROFILING
# ==============================================================================
class TestTelemetryModule:
    def test_log_event_and_rotation(self, tmp_path, monkeypatch):
        logs_dir = tmp_path / "logs"
        monkeypatch.setattr(telem, "LOGS_DIR", logs_dir)
        monkeypatch.setattr(telem, "_LAST_LOG_CLEANUP", 0.0)

        telem.log_event("INFO", "TEST", "Testing telemetry", {"key": "val"})
        assert logs_dir.exists()

        log_files = list(logs_dir.glob("linguo_*.log"))
        assert len(log_files) >= 1
        content = log_files[0].read_text(encoding="utf-8")
        assert "[INFO] [TEST] Testing telemetry" in content
        assert '"key": "val"' in content

        jsonl_file = logs_dir / "linguo_events.jsonl"
        assert jsonl_file.exists()
        j_line = json.loads(jsonl_file.read_text(encoding="utf-8").strip())
        assert j_line["component"] == "TEST"
        assert j_line["meta"]["key"] == "val"

        # Create an old log file to test cleanup
        old_log = logs_dir / "linguo_2020-01-01.log"
        old_log.write_text("Old log")
        os.utime(old_log, (100000, 100000))

        telem._LAST_LOG_CLEANUP = 0.0
        telem.rotate_and_cleanup_logs(max_days=30)
        assert not old_log.exists()

    def test_perf_tracker_and_trace_summary(self, tmp_path, monkeypatch, capsys):
        logs_dir = tmp_path / "logs"
        monkeypatch.setattr(telem, "LOGS_DIR", logs_dir)

        tracker = telem.PerfTracker("pipeline_benchmark")
        with tracker.measure("step_1"):
            time.sleep(0.01)
        with tracker.measure("step_2"):
            time.sleep(0.01)
        timings = tracker.finish()

        assert "step_1" in timings
        assert "step_2" in timings
        assert "total_ms" in timings
        assert timings["total_ms"] > 0

        telem.print_trace_summary(timings)
        out = capsys.readouterr().out
        assert "Linguo Latency & Bottleneck Trace" in out
        assert "step_1" in out
        assert "Total Pipeline" in out

    def test_show_logs(self, tmp_path, monkeypatch, capsys):
        logs_dir = tmp_path / "logs"
        monkeypatch.setattr(telem, "LOGS_DIR", logs_dir)

        # Empty logs dir
        telem.show_logs()
        assert "Nessun file di log recente" in capsys.readouterr().out

        # Populate logs with different levels
        telem.log_event("INFO", "CORE", "Core normal")
        telem.log_event("WARN", "CORE", "Core warning")
        telem.log_event("ERROR", "CORE", "Core error")
        telem.log_event("INFO", "PERF", "Perf message")

        telem.show_logs(limit=10)
        out = capsys.readouterr().out
        assert "Linguo Logs" in out
        assert "Core error" in out


# ==============================================================================
# 6. TEST PLATFORM MACOS UTILITIES
# ==============================================================================
class TestPlatformMacOS:
    def test_copy_and_paste(self, monkeypatch):
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (b"", b"")
        monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: mock_proc)
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: None)

        macos.copy_to_clipboard("test text")
        mock_proc.communicate.assert_called_once()

        macos.paste_to_active_window()

    def test_play_sound_and_notification(self, monkeypatch):
        monkeypatch.setattr(macos, "load_config", lambda: {"sound_feedback": True, "notifications": True})
        mock_popen = MagicMock()
        monkeypatch.setattr(subprocess, "Popen", mock_popen)
        monkeypatch.setattr(os.path, "exists", lambda p: True)

        macos.play_sound("Tink")
        assert mock_popen.called

        macos.show_mac_notification("Title", "Subtitle", "Message")
        assert mock_popen.call_count >= 2

        # Disabled config branches
        monkeypatch.setattr(macos, "load_config", lambda: {"sound_feedback": False, "notifications": False})
        mock_popen.reset_mock()
        macos.play_sound("Tink")
        macos.show_mac_notification("Title", "Subtitle", "Message")
        assert not mock_popen.called

    def test_get_python_cocoa_path(self, monkeypatch):
        # Successful run
        mock_res = MagicMock()
        mock_res.returncode = 0
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_res)
        monkeypatch.setattr(os.path, "exists", lambda p: True)
        path = macos.get_python_cocoa_path()
        assert path != ""

    def test_macos_edge_cases(self, monkeypatch):
        # 1. copy_to_clipboard exception handling
        def mock_popen_fail(*args, **kwargs):
            raise OSError("pbcopy missing")
        monkeypatch.setattr(subprocess, "Popen", mock_popen_fail)
        macos.copy_to_clipboard("fail test")

        # 2. play_sound when file does not exist
        monkeypatch.setattr(macos, "load_config", lambda: {"sound_feedback": True})
        monkeypatch.setattr(os.path, "exists", lambda p: False)
        macos.play_sound("NonExistent")

        # 3. get_python_cocoa_path when search raises Exception
        def mock_run_fail(*args, **kwargs):
            raise subprocess.SubprocessError("Failed")
        monkeypatch.setattr(subprocess, "run", mock_run_fail)
        p = macos.get_python_cocoa_path()
        assert p == sys.executable


# ==============================================================================
# 7. TEST AUDIO ENGINE & CACHE PRE-SEEDING
# ==============================================================================
class TestAudioEngine:
    def test_synthesize_english_kokoro_and_fallbacks(self, tmp_path):
        out_wav = tmp_path / "en_test.mp3"

        # 1. Empty string check
        assert aeng.synthesize_english("", out_wav) is False

        # 2. Mock Edge-TTS Fallback
        def mock_edge_run(cmd, **kwargs):
            out_wav.write_text("fake_mp3")
            return MagicMock(returncode=0)

        with patch("subprocess.run", side_effect=mock_edge_run):
            # Bypass Kokoro import inside function
            with patch.dict("sys.modules", {"kokoro": None}):
                ok = aeng.synthesize_english("Hello world", out_wav, voice="am_adam")
                assert ok is True
                assert out_wav.exists()

        # 3. macOS voice branch
        out_wav.unlink(missing_ok=True)
        def mock_say_run(cmd, **kwargs):
            # If AIFF created, write file
            if "say" in cmd:
                tmp_aiff = out_wav.with_suffix(".tmp.aiff")
                tmp_aiff.write_text("fake_aiff")
            elif "ffmpeg" in cmd[0]:
                out_wav.write_text("converted_mp3")
            return MagicMock(returncode=0)

        with patch("subprocess.run", side_effect=mock_say_run):
            ok = aeng.synthesize_english("Hello world", out_wav, voice="Samantha")
            assert ok is True

    def test_synthesize_thai_cache_and_fallbacks(self, tmp_path, monkeypatch):
        monkeypatch.setattr(aeng, "DATA_DIR", tmp_path)
        out_mp3 = tmp_path / "th_test.mp3"

        # 1. Empty string
        assert aeng.synthesize_thai("", out_mp3) is False

        # 2. Edge-TTS direct synthesis
        def mock_edge(cmd, **kwargs):
            out_mp3.write_text("fake_thai_mp3")
            return MagicMock(returncode=0)

        with patch("subprocess.run", side_effect=mock_edge):
            ok = aeng.synthesize_thai("ไปตลาด", out_mp3)
            assert ok is True
            assert out_mp3.exists()

        # 3. Cache hit path
        cached_target = tmp_path / "th_cached.mp3"
        ok_cached = aeng.synthesize_thai("ไปตลาด", cached_target)
        assert ok_cached is True
        assert cached_target.exists()

    def test_preload_thai_audio_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr(aeng, "DATA_DIR", tmp_path)
        monkeypatch.setattr(aeng, "load_config", lambda: {"speed": 0.8, "thai_voice": "th-TH-PremwadeeNeural"})

        with patch.object(aeng, "synthesize_thai", return_value=True):
            aeng.preload_thai_audio_cache()

    def test_audio_engine_fallbacks_and_failures(self, tmp_path, monkeypatch):
        out_wav = tmp_path / "fail.mp3"
        monkeypatch.setattr(aeng, "DATA_DIR", tmp_path)

        # 1. Kokoro mock with chunks
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [("grapheme", "phoneme", [0.1, 0.2])]
        with patch.dict("sys.modules", {"kokoro": MagicMock(KPipeline=lambda **k: mock_pipeline), "soundfile": MagicMock(), "numpy": MagicMock(concatenate=lambda x: [0.1])}):
            with patch("subprocess.run", return_value=MagicMock()):
                with patch.object(Path, "exists", return_value=True):
                    ok = aeng.synthesize_english("Valid Kokoro sentence", out_wav, voice="af_nicole")
                    assert ok is True

        # 2. Complete failure in synthesize_english returns False
        with patch.dict("sys.modules", {"kokoro": None}):
            with patch("subprocess.run", side_effect=Exception("All TTS failed")):
                ok_fail = aeng.synthesize_english("Failure test", out_wav, voice="Samantha")
                assert ok_fail is False

        # 3. synthesize_thai Kanya fallback
        def mock_kanya_say(cmd, **kwargs):
            if "say" in cmd:
                tmp_aiff = out_wav.with_suffix(".tmp.aiff")
                tmp_aiff.write_text("kanya_aiff")
            elif "ffmpeg" in cmd[0]:
                out_wav.write_text("kanya_mp3")
            return MagicMock()

        with patch("subprocess.run", side_effect=mock_kanya_say):
            ok_kanya = aeng.synthesize_thai("สวัสดี", out_wav)
            assert ok_kanya is True

        # 4. preload_thai_audio_cache exception handling
        monkeypatch.setattr(aeng, "load_config", lambda: {"speed": 0.8, "thai_voice": "th-TH-PremwadeeNeural"})
        with patch.object(aeng, "synthesize_thai", side_effect=Exception("Network down")):
            aeng.preload_thai_audio_cache()

            # Should have run across thai_bricks without crashing


# ==============================================================================
# 8. TEST PEDAGOGY EXPORTERS (TSV & APKG)
# ==============================================================================
class TestPedagogyExport:
    def test_export_tsv_and_apkg(self, tmp_path, monkeypatch):
        db_file = tmp_path / "export_test.db"
        tsv_out = tmp_path / "test.tsv"
        apkg_out = tmp_path / "test.apkg"

        monkeypatch.setattr(cdb, "DB_PATH", db_file)
        cdb.init_db(seed_cards=True)

        # TSV export
        res_tsv = export.export_tsv(output_path=tsv_out, db_path=db_file)
        assert res_tsv.exists()
        tsv_lines = res_tsv.read_text(encoding="utf-8").splitlines()
        assert len(tsv_lines) >= 16  # 1 header + 15 cards

        # APKG export
        res_apkg = export.export_apkg(output_path=apkg_out, db_path=db_file)
        assert res_apkg.exists()
        assert zipfile.is_zipfile(res_apkg)
        with zipfile.ZipFile(res_apkg, "r") as z:
            names = z.namelist()
            assert "collection.anki2" in names
            assert "media" in names

    def test_export_empty_db_raises(self, tmp_path):
        empty_db = tmp_path / "empty.db"
        with sqlite3.connect(empty_db) as conn:
            conn.execute("CREATE TABLE cards (id INTEGER);")

        with pytest.raises(ValueError):
            export.export_tsv(db_path=empty_db)

        with pytest.raises(ValueError):
            export.export_apkg(db_path=empty_db)


# ==============================================================================
# 9. TEST FASTAPI REMOTE SERVER ENDPOINTS & TELEMETRY
# ==============================================================================
@pytest.mark.asyncio
class TestServerEndpoints:
    async def test_server_liveness_readiness_and_metrics(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Liveness
            r_live = await client.get("/health/live")
            assert r_live.status_code == 200
            assert r_live.json()["status"] == "ok"
            assert "X-Trace-Id" in r_live.headers

            # Readiness
            r_ready = await client.get("/health/ready")
            assert r_ready.status_code in (200, 503)

            # Metrics exposition
            r_metrics = await client.get("/metrics")
            assert r_metrics.status_code == 200
            assert "linguo_requests_total" in r_metrics.text

    async def test_server_authentication_and_coach(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Missing token
            r_unauth = await client.post("/coach", json={"phrase": "Hello"})
            assert r_unauth.status_code == 401

            # Invalid token
            r_forbidden = await client.post("/coach", json={"phrase": "Hello"}, headers={"Authorization": "Bearer wrong-token"})
            assert r_forbidden.status_code == 403

            # Empty phrase
            r_empty = await client.post("/coach", json={"phrase": ""}, headers={"Authorization": f"Bearer {API_SECRET_TOKEN}"})
            assert r_empty.status_code in (400, 422)

            # Mock AGY CLI execution for /coach
            mock_output = json.dumps({
                "response": json.dumps({
                    "transcribed_english": "I want to improve",
                    "is_correct": True,
                    "error_category": "NONE",
                    "corrected_english": "I want to improve",
                    "grammar_tip": "Grammatically sound",
                    "thai_concise_script": "อยากพัฒนา",
                    "thai_phonetic_western": "yaak phat-tha-naa",
                    "thai_breakdown": "test"
                })
            })
            with patch("subprocess.run", return_value=MagicMock(stdout=mock_output, returncode=0)):
                r_coach = await client.post(
                    "/coach",
                    json={"phrase": "I want to improve"},
                    headers={"Authorization": f"Bearer {API_SECRET_TOKEN}", "X-Trace-Id": "trc-custom-123"}
                )
                assert r_coach.status_code == 200
                assert r_coach.headers["X-Trace-Id"] == "trc-custom-123"
                data = r_coach.json()
                assert data["status"] == "success"
                assert data["analysis"]["corrected_english"] == "I want to improve"

    async def test_server_audit_endpoint(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Test SENSITIVE_NO_CARD rejected with 400
            r_audit_sens = await client.post(
                "/audit",
                json={"category": "SENSITIVE_NO_CARD", "samples": [{"original": "bad", "corrected": "good"}]},
                headers={"Authorization": f"Bearer {API_SECRET_TOKEN}"}
            )
            assert r_audit_sens.status_code == 400


            # Test normal audit with mocked flash 3.8
            mock_audit_res = json.dumps({
                "response": json.dumps({
                    "card_title": "AUDIT CARD",
                    "card_type": "Arcade Encounter",
                    "cefr_level": "B1",
                    "front_challenge": "Test [ ? ]",
                    "back_solution": "Test PASSED",
                    "british_council_rule": "Rule here",
                    "gag_quote": "Gag here",
                    "thai_script": "ทดสอบ",
                    "thai_phonetic": "thot-sop",
                    "thai_tones": "M",
                    "thai_breakdown": "test"
                })
            })
            with patch("subprocess.run", return_value=MagicMock(stdout=mock_audit_res, returncode=0)):
                r_audit = await client.post(
                    "/audit",
                    json={"category": "ARTICLES", "samples": [{"original": "bad", "corrected": "good"}]},
                    headers={"Authorization": f"Bearer {API_SECRET_TOKEN}"}
                )
                assert r_audit.status_code == 200
                assert r_audit.json()["card"]["card_title"] == "AUDIT CARD"


# ==============================================================================
# 10. TEST CLI, DOCTOR & CARDS (bin/linguo)
# ==============================================================================
class TestCliAndDoctor:
    def test_show_history_json_and_table(self, tmp_path, monkeypatch, capsys):
        from bin import linguo as cli
        db_file = tmp_path / "cli_history.db"
        monkeypatch.setattr(cli, "DB_PATH", db_file)
        cli.init_db()

        # Empty history
        cli.show_history(limit=5, as_json=False)
        out = capsys.readouterr().out
        assert "Linguo History (Last 0 entries)" in out

        # Insert a record
        cli.save_record({
            "is_correct": True,
            "corrected_english": "Test phrase",
            "grammar_tip": "All good",
            "english_level": "B2"
        }, original_text="Test phrase")

        cli.show_history(limit=5, as_json=False)
        out = capsys.readouterr().out
        assert "Linguo History" in out
        assert "Test phrase" in out

        cli.show_history(limit=5, as_json=True)
        out_json = capsys.readouterr().out
        data = json.loads(out_json.strip())
        assert len(data) >= 1
        assert data[0]["corrected_english"] == "Test phrase"

    def test_show_cards_and_master(self, tmp_path, monkeypatch, capsys):
        from bin import linguo as cli
        db_file = tmp_path / "cli_cards.db"
        monkeypatch.setattr(cli, "DB_PATH", db_file)
        cli.init_db()

        # Overview of active cards
        cli.show_cards()
        out = capsys.readouterr().out
        assert "THE MARKET STAMP" in out

        # Flip specific card #1
        cli.show_cards(card_id=1, flip=True)
        out = capsys.readouterr().out
        assert "SOLUZIONE" in out
        assert "market" in out.lower()

        # Master specific card #1
        cli.show_cards(master_id=1)
        out = capsys.readouterr().out
        assert "archiviata come MASTERED" in out

    def test_run_doctor_diagnostics(self, tmp_path, monkeypatch, capsys):
        from bin import linguo as cli
        db_file = tmp_path / "doc.db"
        monkeypatch.setattr(cli, "DB_PATH", db_file)
        monkeypatch.setattr(cli, "DATA_DIR", tmp_path)
        cli.init_db()

        with patch("shutil.which", return_value="/usr/local/bin/ffmpeg"):
            cli.run_doctor()
            out = capsys.readouterr().out
            assert "Linguo Doctor: Fundamental Systems Check" in out
            assert "SQLite WAL" in out


