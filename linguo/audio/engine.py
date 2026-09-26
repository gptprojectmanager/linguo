"""
Linguo Audio Engine
Hybrid TTS: Kokoro-82M Local Neural (English, 2 CPU threads) + Edge-TTS (Thai studio).
Includes fallback to macOS 'say' / afplay.
"""

import os
import sys
import shutil
import hashlib
import sqlite3
import subprocess
from pathlib import Path
from ..core.config import DATA_DIR, AUDIO_DIR, DB_PATH, load_config
from ..core.db import init_db

FFMPEG_BIN = "/opt/local/bin/ffmpeg" if os.path.exists("/opt/local/bin/ffmpeg") else "ffmpeg"


def synthesize_english(text: str, output_path: Path, voice: str = "af_nicole", speed: float = 0.8) -> bool:
    """Synthesizes English speech via Kokoro-82M, Edge-TTS, or macOS say."""
    if not text:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    is_macos_voice = voice in ("Samantha", "Alex", "Victoria", "Daniel")

    # 1. Kokoro-82M Local Neural
    if not is_macos_voice:
        try:
            import torch
            torch.set_num_threads(2)
            from kokoro import KPipeline
            import soundfile as sf
            import numpy as np

            pipeline = KPipeline(lang_code='a')
            kokoro_voice = voice if voice in ("af_nicole", "am_adam") else "af_nicole"
            generator = pipeline(text, voice=kokoro_voice, speed=speed)
            audio_chunks = [audio for _, _, audio in generator]
            if audio_chunks:
                tmp_wav = output_path.with_suffix(".tmp.wav")
                sf.write(str(tmp_wav), np.concatenate(audio_chunks), 24000)
                subprocess.run([FFMPEG_BIN, "-i", str(tmp_wav), "-y", str(output_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                tmp_wav.unlink(missing_ok=True)
                if output_path.exists():
                    return True
        except Exception:
            pass

    # 2. Edge-TTS Fallback
    if not is_macos_voice:
        try:
            rate_percent = int((speed - 1.0) * 100)
            rate_str = f"{rate_percent:+d}%" if rate_percent != 0 else "+0%"
            v = "en-US-GuyNeural" if voice == "am_adam" else "en-US-JennyNeural"
            subprocess.run([
                "edge-tts",
                "--voice", v,
                f"--rate={rate_str}",
                "--text", text,
                "--write-media", str(output_path)
            ], capture_output=True, timeout=8.0, check=True)
            if output_path.exists():
                return True
        except Exception:
            pass

    # 3. macOS say Fallback
    try:
        say_voice = voice if is_macos_voice else ("Alex" if "adam" in voice or "male" in voice else "Samantha")
        say_rate = str(int(175 * speed))
        tmp_aiff = output_path.with_suffix(".tmp.aiff")
        subprocess.run(["say", "-v", say_voice, "-r", say_rate, text, "-o", str(tmp_aiff)], timeout=5.0)
        if tmp_aiff.exists():
            subprocess.run([FFMPEG_BIN, "-i", str(tmp_aiff), "-y", str(output_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            tmp_aiff.unlink(missing_ok=True)
            return output_path.exists()
    except Exception:
        pass

    return False


def synthesize_thai(text: str, output_path: Path, voice: str = "th-TH-PremwadeeNeural", speed: float = 0.8) -> bool:
    """Synthesizes Thai speech via Edge-TTS (with disk caching) or macOS say (Kanya)."""
    if not text:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    thai_cache_dir = DATA_DIR / "cache" / "thai"
    thai_cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.md5(f"{text.strip()}_{speed}".encode("utf-8")).hexdigest()
    cached_file = thai_cache_dir / f"{cache_key}.mp3"

    if cached_file.exists():
        try:
            shutil.copyfile(str(cached_file), str(output_path))
            return output_path.exists()
        except Exception:
            pass

    # 1. Edge-TTS Studio Neural
    try:
        v = voice if voice.startswith("th-") else "th-TH-PremwadeeNeural"
        rate_percent = int((speed - 1.0) * 100)
        rate_str = f"{rate_percent:+d}%" if rate_percent != 0 else "+0%"
        subprocess.run([
            "edge-tts",
            "--voice", v,
            f"--rate={rate_str}",
            "--text", text,
            "--write-media", str(output_path)
        ], capture_output=True, timeout=8.0, check=True)
        if output_path.exists():
            try:
                shutil.copyfile(str(output_path), str(cached_file))
            except Exception:
                pass
            return True
    except Exception:
        pass

    # 2. macOS say (Kanya) Fallback
    try:
        say_rate = str(int(175 * speed))
        thai_tmp_aiff = output_path.with_suffix(".tmp.aiff")
        subprocess.run(["say", "-v", "Kanya", "-r", say_rate, text, "-o", str(thai_tmp_aiff)], timeout=5.0)
        if thai_tmp_aiff.exists():
            subprocess.run([FFMPEG_BIN, "-i", str(thai_tmp_aiff), "-filter:a", "volume=2.2,aresample=24000", "-y", str(output_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            thai_tmp_aiff.unlink(missing_ok=True)
            return output_path.exists()
    except Exception:
        pass

    return False


def preload_thai_audio_cache():
    """Warms up local cache for common Thai grammatical building blocks."""
    thai_bricks = [
        "ไป", "มา", "กิน", "ดื่ม", "อยาก", "ชอบ", "มี", "ไม่มี", "ใช่", "ไม่ใช่",
        "ตลาด", "บ้าน", "กาแฟ", "น้ำ", "ห้องน้ำ", "เท่าไหร่", "ลดได้ไหม",
        "อร่อย", "เผ็ด", "ไม่เผ็ด", "ขอบคุณ", "สวัสดี", "ขอโทษ", "ช่วยด้วย"
    ]
    thai_cache_dir = DATA_DIR / "cache" / "thai"
    thai_cache_dir.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    speed = float(cfg.get("speed", 0.8))
    voice = cfg.get("thai_voice", "th-TH-PremwadeeNeural")

    print(f"\n🎧 \033[1;36mPreriscaldamento cache audio Thai ({len(thai_bricks)} blocchi canonici)...\033[0m")
    cached = 0
    skipped = 0
    for text in thai_bricks:
        cache_key = hashlib.md5(f"{text.strip()}_{speed}".encode("utf-8")).hexdigest()
        target_file = thai_cache_dir / f"{cache_key}.mp3"
        if target_file.exists():
            skipped += 1
            continue
        try:
            if synthesize_thai(text, target_file, voice=voice, speed=speed):
                cached += 1
                print(f"  ✨ {text}")
        except Exception as e:
            sys.stderr.write(f"  ❌ Errore su '{text}': {e}\n")

    print(f"\n🎉 \033[1;32mCompletato:\033[0m {cached} nuovi mattoni memorizzati, {skipped} già presenti.")
    print(f"📁 Directory cache: \033[90m{thai_cache_dir}\033[0m\n")
