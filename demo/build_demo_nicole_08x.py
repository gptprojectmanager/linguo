import os
import subprocess
from pathlib import Path

DEST_DIR = Path("/Users/sam/Desktop/Linguo_Poem_Demos")
DEST_DIR.mkdir(parents=True, exist_ok=True)

ENG_POEM = """I learned how to leave,
how to sleep alone,
how to carry my life
without asking for help.

Then you came close,
your body warm against mine,
and I learned a harder courage:

not to run from love."""

THAI_POEM = """ฉันเรียนรู้ที่จะจากไป
เรียนรู้ที่จะนอนเพียงลำพัง
แบกรับชีวิตของตัวเอง... โดยไม่เอ่ยขอความช่วยเหลือ

แล้วเธอก็ก้าวเข้ามาใกล้
ไออุ่นจากกายเธอแนบชิดกับฉัน
และฉันก็ได้เรียนรู้ความกล้าหาญที่ยากยิ่งกว่า...

นั่นคือการไม่วิ่งหนีความรัก"""

ffmpeg_bin = "/opt/local/bin/ffmpeg" if os.path.exists("/opt/local/bin/ffmpeg") else "ffmpeg"

def render_english_nicole_08x():
    import torch
    torch.set_num_threads(2)
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np

    print("Synthesizing English with Kokoro (af_nicole) at 0.8x speed...")
    pipeline = KPipeline(lang_code='a')
    generator = pipeline(ENG_POEM, voice='af_nicole', speed=0.8)
    chunks = [audio for _, _, audio in generator]
    if chunks:
        wav_path = DEST_DIR / "eng_nicole_08_tmp.wav"
        mp3_path = DEST_DIR / "POESIA_1_ENG_Nicole_0.8x.mp3"
        sf.write(str(wav_path), np.concatenate(chunks), 24000)
        subprocess.run([
            ffmpeg_bin, "-i", str(wav_path),
            "-codec:a", "libmp3lame", "-qscale:a", "2",
            "-y", str(mp3_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        wav_path.unlink(missing_ok=True)
        print(f"✅ Created: {mp3_path.name}")
        return mp3_path
    return None

def render_thai_premwadee_08x():
    print("Synthesizing Thai with Edge-TTS (th-TH-PremwadeeNeural) at 0.8x (-20%)...")
    mp3_path = DEST_DIR / "POESIA_2_THAI_Premwadee_0.8x.mp3"
    subprocess.run([
        "edge-tts",
        "--voice", "th-TH-PremwadeeNeural",
        "--rate=-20%",
        "--text", THAI_POEM,
        "--write-media", str(mp3_path)
    ], check=True)
    print(f"✅ Created: {mp3_path.name}")
    return mp3_path

def assemble_duet_08x(eng_path, thai_path):
    print("Assembling Duet at 0.8x...")
    duet_path = DEST_DIR / "DUETTO_PERFETTO_Nicole0.8x_Premwadee0.8x.mp3"
    silence_wav = DEST_DIR / "silence_tmp.wav"
    subprocess.run([
        ffmpeg_bin, "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2.2",
        "-y", str(silence_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    concat_file = DEST_DIR / "concat_tmp.txt"
    concat_file.write_text(f"file '{eng_path.resolve()}'\nfile '{silence_wav.resolve()}'\nfile '{thai_path.resolve()}'\n", encoding="utf-8")

    subprocess.run([
        ffmpeg_bin, "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:a", "libmp3lame", "-q:a", "2",
        "-y", str(duet_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    silence_wav.unlink(missing_ok=True)
    concat_file.unlink(missing_ok=True)
    print(f"✅ Created: {duet_path.name}")
    return duet_path

if __name__ == "__main__":
    eng = render_english_nicole_08x()
    thai = render_thai_premwadee_08x()
    if eng and thai:
        assemble_duet_08x(eng, thai)
    print("\n🎉 Tutti i file a 0.8x pronti sul Desktop!")
