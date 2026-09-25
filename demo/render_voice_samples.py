import os
import sys
import subprocess
from pathlib import Path

OUT_DIR = Path("/Users/sam/Desktop/Linguo_Poem_Demos/voice_samples")
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

        print(f"Synthesizing Kokoro voice: {voice_name}...")
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
        print(f"Synthesizing Edge voice: {voice_name}...")
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
    # Top full, resonant voices:
    # 1. am_adam: Deep baritone, warm, very full body
    render_kokoro("am_adam", "1_kokoro_am_adam_deep_baritone")
    
    # 2. am_michael: Natural, rich, warm American male
    render_kokoro("am_michael", "2_kokoro_am_michael_warm_rich")

    # 3. bm_george: Deep British storytelling / audiobook voice
    render_kokoro("bm_george", "3_kokoro_bm_george_british_deep")

    # 4. af_bella: Warmer, fuller, more mature female voice
    render_kokoro("af_bella", "4_kokoro_af_bella_warm_female")

    # 5. en-US-ChristopherNeural: Deep, resonant, cinematic storytelling
    render_edge("en-US-ChristopherNeural", "5_edge_christopher_cinematic_deep")

    # 6. en-US-GuyNeural: Warm, rounded, classic radio narrator
    render_edge("en-US-GuyNeural", "6_edge_guy_warm_rounded")

    # 7. en-GB-RyanNeural: British deep, emotive baritone
    render_edge("en-GB-RyanNeural", "7_edge_ryan_british_baritone")

    print("\nAll voice audition samples created in:", OUT_DIR)
