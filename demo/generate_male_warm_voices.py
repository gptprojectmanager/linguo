import os
import sys
import subprocess
from pathlib import Path

OUT_DIR = Path("/Users/sam/Desktop/Linguo_Poem_Demos/male_warm_voices")
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

        print(f"Synthesizing Kokoro male voice: {voice_name}...")
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
        print(f"Synthesizing Edge-TTS male voice: {voice_name}...")
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
    # 1. Edge-TTS: en-US-ChristopherNeural (Baritono caldissimo, profondo, cinematografico)
    render_edge("en-US-ChristopherNeural", "1_edge_christopher_baritono_caldissimo")

    # 2. Edge-TTS: en-US-GuyNeural (Caldo, rotondo, naturale e rilassante)
    render_edge("en-US-GuyNeural", "2_edge_guy_caldo_rotondo")

    # 3. Kokoro: am_adam (Baritono profondo, corposo, maturo)
    render_kokoro("am_adam", "3_kokoro_am_adam_profondo_corposo")

    # 4. Kokoro: am_michael (Caldo, intimo, conversazionale)
    render_kokoro("am_michael", "4_kokoro_am_michael_intimo_caldo")

    # 5. Kokoro: bm_george (Narratore britannico profondo, stile audiolibro)
    render_kokoro("bm_george", "5_kokoro_bm_george_narratore_britannico")

    # 6. Edge-TTS: en-GB-RyanNeural (Poeta britannico, caldo, espressivo)
    render_edge("en-GB-RyanNeural", "6_edge_ryan_britannico_espressivo")

    print("\n🎉 Campioni di voci maschili calde creati in:", OUT_DIR)
