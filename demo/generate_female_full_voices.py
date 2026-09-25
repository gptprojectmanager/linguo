import os
import sys
import subprocess
from pathlib import Path

OUT_DIR = Path("/Users/sam/Desktop/Linguo_Poem_Demos/female_full_voices")
OUT_DIR.mkdir(parents=True, exist_ok=True)

POEM = """I learned how to leave,
how to sleep alone,
how to carry my life
without asking for help.

Then you came close,
your body warm against mine,
and I learned a harder courage:

not to run from love."""

ffmpeg_bin = "/opt/local/bin/ffmpeg" if os.path.exists("/opt/local/bin/ffmpeg") else "ffmpeg"

def render_kokoro(voice_name, filename, speed=0.92):
    try:
        import torch
        torch.set_num_threads(2)
        from kokoro import KPipeline
        import soundfile as sf
        import numpy as np

        print(f"Synthesizing Kokoro female voice: {voice_name}...")
        pipeline = KPipeline(lang_code='b' if voice_name.startswith('b') else 'a')
        generator = pipeline(POEM, voice=voice_name, speed=speed)
        chunks = [audio for _, _, audio in generator]
        if chunks:
            wav_path = OUT_DIR / f"{filename}.wav"
            mp3_path = OUT_DIR / f"{filename}.mp3"
            sf.write(str(wav_path), np.concatenate(chunks), 24000)
            subprocess.run([
                ffmpeg_bin, "-i", str(wav_path),
                "-codec:a", "libmp3lame", "-qscale:a", "2",
                "-y", str(mp3_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            wav_path.unlink(missing_ok=True)
            print(f"  -> Created {mp3_path.name}")
            return mp3_path
    except Exception as e:
        print(f"  Failed Kokoro {voice_name}: {e}")
    return None

def render_edge(voice_name, filename, rate="-6%"):
    try:
        print(f"Synthesizing Edge-TTS female voice: {voice_name}...")
        mp3_path = OUT_DIR / f"{filename}.mp3"
        subprocess.run([
            "edge-tts",
            "--voice", voice_name,
            f"--rate={rate}",
            "--text", POEM,
            "--write-media", str(mp3_path)
        ], check=True)
        print(f"  -> Created {mp3_path.name}")
        return mp3_path
    except Exception as e:
        print(f"  Failed Edge {voice_name}: {e}")
    return None

if __name__ == "__main__":
    # 1. Kokoro: af_bella (Calda, piena, rotonda, meno acuta di af_heart)
    render_kokoro("af_bella", "1_kokoro_af_bella_calda_e_piena")

    # 2. Kokoro: af_nicole (Profonda, vellutata, matura, calma)
    render_kokoro("af_nicole", "2_kokoro_af_nicole_profonda_vellutata")

    # 3. Kokoro: af_sarah (Naturale, corpo morbido, riflessiva)
    render_kokoro("af_sarah", "3_kokoro_af_sarah_morbida_corposa")

    # 4. Kokoro: bf_emma (Letteraria britannica, profonda, elegante)
    render_kokoro("bf_emma", "4_kokoro_bf_emma_british_profonda")

    # 5. Edge-TTS: en-US-AvaNeural (Corposa, calda, respiro naturale ad alta fedeltà)
    render_edge("en-US-AvaNeural", "5_edge_ava_calda_espressiva")

    # 6. Edge-TTS: en-GB-SoniaNeural (Britannica vellutata, profonda e intima)
    render_edge("en-GB-SoniaNeural", "6_edge_sonia_british_vellutata")

    print("\n🎉 Campioni di voci femminili piene creati in:", OUT_DIR)
