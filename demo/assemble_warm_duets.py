import os
import subprocess
from pathlib import Path

DEST_DIR = Path("/Users/sam/Desktop/Linguo_Poem_Demos")
FEMALE_DIR = DEST_DIR / "female_full_voices"
MALE_DIR = DEST_DIR / "male_warm_voices"
THAI_MP3 = DEST_DIR / "poem_thai.mp3"

ffmpeg_bin = "/opt/local/bin/ffmpeg" if os.path.exists("/opt/local/bin/ffmpeg") else "ffmpeg"

def concat_duet(eng_mp3_path, out_duet_path, pause_sec=2.2):
    silence_wav = DEST_DIR / "temp_silence.wav"
    subprocess.run([
        ffmpeg_bin, "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(pause_sec),
        "-y", str(silence_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    concat_file = DEST_DIR / "temp_concat.txt"
    concat_file.write_text(f"file '{eng_mp3_path.resolve()}'\nfile '{silence_wav.resolve()}'\nfile '{THAI_MP3.resolve()}'\n", encoding="utf-8")

    subprocess.run([
        ffmpeg_bin, "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:a", "libmp3lame", "-q:a", "2",
        "-y", str(out_duet_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    silence_wav.unlink(missing_ok=True)
    concat_file.unlink(missing_ok=True)
    print(f"✅ Duetto generato: {out_duet_path.name}")

if __name__ == "__main__":
    # 1. Master Duetto Femminile (Studio Caldo: Ava Neural + Thai Premwadee)
    ava_eng = FEMALE_DIR / "5_edge_ava_calda_espressiva.mp3"
    if ava_eng.exists():
        concat_duet(ava_eng, DEST_DIR / "DUETTO_1_FEMMINILE_CALDA_Ava_Thai.mp3")

    # 2. Master Duetto Maschile (Baritono Caldissimo: Christopher Neural + Thai Premwadee)
    chris_eng = MALE_DIR / "1_edge_christopher_baritono_caldissimo.mp3"
    if chris_eng.exists():
        concat_duet(chris_eng, DEST_DIR / "DUETTO_2_MASCHILE_MOLTO_CALDA_Christopher_Thai.mp3")

    # 3. Master Duetto Kokoro Offline Femminile (af_bella + Thai)
    bella_eng = FEMALE_DIR / "1_kokoro_af_bella_calda_e_piena.mp3"
    if bella_eng.exists():
        concat_duet(bella_eng, DEST_DIR / "DUETTO_3_KOKORO_OFFLINE_FEMALE_Bella_Thai.mp3")

    # 4. Master Duetto Kokoro Offline Maschile (am_adam baritono profondo + Thai)
    adam_eng = MALE_DIR / "3_kokoro_am_adam_profondo_corposo.mp3"
    if adam_eng.exists():
        concat_duet(adam_eng, DEST_DIR / "DUETTO_4_KOKORO_OFFLINE_MALE_Adam_Thai.mp3")

    print("\nTutti i duetti pronti sul Desktop!")
