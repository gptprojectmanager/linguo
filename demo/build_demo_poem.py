import os
import sys
import asyncio
import subprocess
from pathlib import Path

OUT_DIR = Path("/Users/sam/linguo/demo")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENG_POEM = """I learned how to leave,
how to sleep alone,
how to carry my life
without asking for help.

Then you came close,
your body warm against mine,
and I learned a harder courage:

not to run from love."""

# Poetic and emotionally resonant Thai translation
THAI_POEM = """ฉันเรียนรู้ที่จะจากไป
เรียนรู้ที่จะนอนเพียงลำพัง
แบกรับชีวิตของตัวเอง... โดยไม่เอ่ยขอความช่วยเหลือ

แล้วเธอก็ก้าวเข้ามาใกล้
ไออุ่นจากกายเธอแนบชิดกับฉัน
และฉันก็ได้เรียนรู้ความกล้าหาญที่ยากยิ่งกว่า...

นั่นคือการไม่วิ่งหนีความรัก"""

def generate_english():
    import torch
    torch.set_num_threads(2)
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np

    print("Generating English audio with Kokoro-82M (af_heart)...")
    pipeline = KPipeline(lang_code='a')
    generator = pipeline(ENG_POEM, voice='af_heart', speed=0.92)
    audio_chunks = [audio for _, _, audio in generator]
    if audio_chunks:
        wav_path = OUT_DIR / "poem_eng_tmp.wav"
        mp3_path = OUT_DIR / "poem_english.mp3"
        sf.write(str(wav_path), np.concatenate(audio_chunks), 24000)
        ffmpeg_bin = "/opt/local/bin/ffmpeg" if os.path.exists("/opt/local/bin/ffmpeg") else "ffmpeg"
        subprocess.run([
            ffmpeg_bin, "-i", str(wav_path),
            "-codec:a", "libmp3lame", "-qscale:a", "2",
            "-y", str(mp3_path)
        ], check=True)
        wav_path.unlink(missing_ok=True)
        print(f"✅ English MP3 created: {mp3_path}")
        return mp3_path
    return None

def generate_thai():
    print("Generating Thai audio with Edge-TTS (th-TH-PremwadeeNeural)...")
    mp3_path = OUT_DIR / "poem_thai.mp3"
    cmd = [
        "edge-tts",
        "--voice", "th-TH-PremwadeeNeural",
        "--rate=-8%",
        "--pitch=+0Hz",
        "--text", THAI_POEM,
        "--write-media", str(mp3_path)
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Thai MP3 created: {mp3_path}")
    return mp3_path

def combine_audio(eng_file, thai_file):
    print("Combining English + Thai with artistic pause...")
    ffmpeg_bin = "/opt/local/bin/ffmpeg" if os.path.exists("/opt/local/bin/ffmpeg") else "ffmpeg"
    combined_path = OUT_DIR / "poem_english_thai_duet.mp3"
    
    # 2 seconds silence
    silence_wav = OUT_DIR / "silence.wav"
    subprocess.run([
        ffmpeg_bin, "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2.0",
        "-y", str(silence_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Concat eng + silence + thai
    concat_list = OUT_DIR / "concat.txt"
    concat_list.write_text(f"file '{eng_file.resolve()}'\nfile '{silence_wav.resolve()}'\nfile '{thai_file.resolve()}'\n", encoding="utf-8")
    
    subprocess.run([
        ffmpeg_bin, "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "libmp3lame", "-q:a", "2",
        "-y", str(combined_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    silence_wav.unlink(missing_ok=True)
    concat_list.unlink(missing_ok=True)
    print(f"✅ Combined MP3 created: {combined_path}")
    return combined_path

if __name__ == "__main__":
    eng_mp3 = generate_english()
    thai_mp3 = generate_thai()
    if eng_mp3 and thai_mp3:
        combine_audio(eng_mp3, thai_mp3)
    print("🎉 All demo MP3s generated successfully in", OUT_DIR)
