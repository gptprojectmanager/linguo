import os
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

OUT_DIR = Path("/Users/sam/Desktop/Linguo_Poem_Demos/thai_voice_variations")
OUT_DIR.mkdir(parents=True, exist_ok=True)

THAI_POEM = """ฉันเรียนรู้ที่จะจากไป
เรียนรู้ที่จะนอนเพียงลำพัง
แบกรับชีวิตของตัวเอง... โดยไม่เอ่ยขอความช่วยเหลือ

แล้วเธอก็ก้าวเข้ามาใกล้
ไออุ่นจากกายเธอแนบชิดกับฉัน
และฉันก็ได้เรียนรู้ความกล้าหาญที่ยากยิ่งกว่า...

นั่นคือการไม่วิ่งหนีความรัก"""

ffmpeg_bin = "/opt/local/bin/ffmpeg" if os.path.exists("/opt/local/bin/ffmpeg") else "ffmpeg"

def render_edge(voice, rate, filename, warm_eq=False):
    print(f"Synthesizing Thai Edge: {voice} (rate: {rate}, warm_eq={warm_eq})...")
    tmp_path = OUT_DIR / f"{filename}_raw.mp3"
    mp3_path = OUT_DIR / f"{filename}.mp3"
    cmd = [
        "edge-tts",
        "--voice", voice,
        f"--rate={rate}",
        "--text", THAI_POEM,
        "--write-media", str(tmp_path if warm_eq else mp3_path)
    ]
    subprocess.run(cmd, check=True)

    if warm_eq:
        # Boost warm low-mids (+3.5dB at 250Hz, +2dB at 500Hz) for velvety fullness
        subprocess.run([
            ffmpeg_bin, "-i", str(tmp_path),
            "-af", "equalizer=f=250:t=q:w=1:g=3.5,equalizer=f=500:t=q:w=1:g=2,volume=1.2",
            "-y", str(mp3_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        tmp_path.unlink(missing_ok=True)

    print(f"  -> Created {mp3_path.name}")
    return mp3_path

def render_google_tts():
    try:
        print("Synthesizing Thai Google TTS (Voce diversa)...")
        mp3_path = OUT_DIR / "5_thai_google_female_voce_alternativa.mp3"
        url = "https://translate.google.com/translate_tts?ie=UTF-8&q=" + urllib.parse.quote(THAI_POEM) + "&tl=th&client=tw-ob"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp, open(mp3_path, 'wb') as f:
            f.write(resp.read())
        print(f"  -> Created {mp3_path.name}")
        return mp3_path
    except Exception as e:
        print(f"  Failed Google TTS: {e}")
        return None

def render_say_kanya():
    try:
        print("Synthesizing macOS Kanya (Apple locale)...")
        aiff_path = OUT_DIR / "kanya_tmp.aiff"
        mp3_path = OUT_DIR / "6_thai_macos_kanya_apple.mp3"
        subprocess.run(["say", "-v", "Kanya", "-r", "150", THAI_POEM, "-o", str(aiff_path)], check=True)
        subprocess.run([ffmpeg_bin, "-i", str(aiff_path), "-filter:a", "volume=2.2", "-y", str(mp3_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        aiff_path.unlink(missing_ok=True)
        print(f"  -> Created {mp3_path.name}")
        return mp3_path
    except Exception as e:
        print(f"  Failed Kanya: {e}")
        return None

if __name__ == "__main__":
    # 1. Edge-TTS: Premwadee Femminile Naturale (quella usata prima)
    render_edge("th-TH-PremwadeeNeural", "-8%", "1_thai_premwadee_femminile_naturale")

    # 2. Edge-TTS: Premwadee Femminile Calda & Vellutata (EQ caldo a corpo pieno)
    render_edge("th-TH-PremwadeeNeural", "-10%", "2_thai_premwadee_femminile_calda_vellutata", warm_eq=True)

    # 3. Edge-TTS: Niwat Maschile Caldo (Voce Maschile Thailandese!)
    render_edge("th-TH-NiwatNeural", "-6%", "3_thai_niwat_maschile_caldo")

    # 4. Edge-TTS: Niwat Maschile Profondo / Poeta (Voce Maschile corposa e narrativa)
    render_edge("th-TH-NiwatNeural", "-9%", "4_thai_niwat_maschile_profondo_narratore", warm_eq=True)

    # 5. Google TTS: Voce Femminile Google (differente attrice/modello da Microsoft)
    render_google_tts()

    # 6. Apple macOS: Kanya
    render_say_kanya()

    print("\nTutte le 6 alternative di voci Thailandesi pronte in:", OUT_DIR)
