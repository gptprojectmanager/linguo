"""
Linguo Configuration & Directory Resolution
Provides configuration persistence, environment overrides, and CLI inspection.
"""

import os
import json
from pathlib import Path

# Base Paths (Environment variables allow sandboxed E2E testing without host pollution)
DATA_DIR = Path(os.environ.get("LINGUO_DATA_DIR", Path.home() / ".local" / "share" / "linguo"))
AUDIO_DIR = DATA_DIR / "audio"
DB_PATH = DATA_DIR / "history.db"
LOG_PATH = DATA_DIR / "history.md"
CONFIG_PATH = DATA_DIR / "config.json"
WORKSPACE_DIR = Path(os.environ.get("LINGUO_WORKSPACE_DIR", DATA_DIR / "workspace"))
LOGS_DIR = DATA_DIR / "logs"

DEFAULT_CONFIG = {
    "hotkey": "<ctrl>+<alt>+<space>",
    "auto_paste": True,
    "sound_feedback": True,
    "tts_engine": "hybrid",  # "hybrid" = Kokoro-82M (English local) + Edge-TTS (Thai studio)
    "eng_voice": "af_nicole", # "af_nicole" | "Samantha" | "am_adam" | "Alex"
    "thai_voice": "th-TH-PremwadeeNeural", # Edge-TTS Thai voice
    "speed": 0.8,            # 0.8x playback speed for clear didactic articulation
    "notifications": True,
    "model": "gemini-3.6-flash-low",       # Real-time coach model (Fast 3.6 / Balanced 3.7 / Deep 3.8)
    "card_model": "gemini-3.8-flash-high", # Card & Graphic production quality (canon / 3.7 / 3.8)
    "dispatch_mode": "auto"  # "auto" | "dell" | "local"
}


def load_config() -> dict:
    """Loads JSON configuration with fallback to default settings."""
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    """Persists configuration to JSON file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def show_config_cli(subargs: list[str]):
    """Inspects or updates the Linguo configuration matrix with deterministic feedback."""
    cfg = load_config()

    if not subargs:
        print("\n\033[1;34m─── Linguo Configuration Matrix (Operativo) ───\033[0m")
        model = cfg.get("model", "gemini-3.6-flash-low")
        card_model = cfg.get("card_model", "gemini-3.8-flash-high")
        tts = cfg.get("tts_engine", "hybrid")
        speed = cfg.get("speed", 0.8)
        eng_voice = cfg.get("eng_voice", "af_nicole")
        thai_voice = cfg.get("thai_voice", "th-TH-PremwadeeNeural")
        route = cfg.get("dispatch_mode", "auto")
        auto_paste = cfg.get("auto_paste", True)
        sound = cfg.get("sound_feedback", True)
        notify = cfg.get("notifications", True)
        hotkey = cfg.get("hotkey", "<ctrl>+<alt>+<space>")

        print(f"  \033[1m1. Coach Model:\033[0m       \033[1;32m{model:<22}\033[0m [Opzioni: gemini-3.6-flash-low (⚡ Fast 3.6 Low), gemini-3.7-flash-medium (⚖️ Balanced), gemini-3.8-flash-high (🧠 Deep 3.8 Pro)]")
        print(f"  \033[1m2. Card Production:\033[0m   \033[1;32m{card_model:<22}\033[0m [Opzioni: canon (⚡ 0 Token / Istantaneo), gemini-3.7-flash-medium (⚖️ Balanced), gemini-3.8-flash-high (🔬 Studio High)]")
        print(f"  \033[1m3. TTS Engine:\033[0m        \033[1;32m{tts:<22}\033[0m [Opzioni: hybrid (Kokoro+Edge), local (Say offline), edge (Azure Cloud)]")
        print(f"  \033[1m4. Playback Speed:\033[0m    \033[1;32m{str(speed) + 'x':<22}\033[0m [Opzioni: 0.75 (lenta), 0.8 (didattica), 1.0 (naturale)]")
        print(f"  \033[1m5. English Voice:\033[0m     \033[1;32m{eng_voice:<22}\033[0m [Opzioni: 👩 af_nicole (Studio Neural), 👩 Samantha (macOS Built-in), 👨 am_adam (Studio Neural), 👨 Alex (macOS Built-in)]")
        print(f"  \033[1m6. Thai Voice:\033[0m        \033[1;32m{thai_voice:<22}\033[0m [Opzioni: th-TH-PremwadeeNeural (Edge Studio), Kanya (Say offline)]")
        print(f"  \033[1m7. Dispatch Route:\033[0m    \033[1;32m{route:<22}\033[0m [Opzioni: auto (Cascade WG->CF->Local), dell (Force Server), local (Force Mac)]")
        print(f"  \033[1m8. Auto-Paste:\033[0m        \033[1;32m{str(auto_paste):<22}\033[0m [Opzioni: on, off]")
        print(f"  \033[1m9. Sound Feedback:\033[0m    \033[1;32m{str(sound):<22}\033[0m [Opzioni: on, off]")
        print(f" \033[1m10. Notifications:\033[0m     \033[1;32m{str(notify):<22}\033[0m [Opzioni: on, off]")
        print(f" \033[1m11. Global Hotkey:\033[0m     \033[1;32m{hotkey:<22}\033[0m")
        print(f"\n📁 File di configurazione: \033[36m{CONFIG_PATH}\033[0m")
        print("💡 Modifica: \033[1mlinguo config <parametro> <valore>\033[0m  (es: linguo config model balanced, linguo config card canon, linguo config voice adam)\n")
        return

    key = subargs[0].lower().strip()
    val = subargs[1].lower().strip() if len(subargs) > 1 else ""

    if key == "reset":
        save_config(DEFAULT_CONFIG)
        print("✅ Configurazione ripristinata ai valori predefiniti di fabbrica.")
        return

    if not val:
        print(f"⚠️ Specifica un valore per '{key}'. Esempio: linguo config {key} <valore>")
        return

    if key in ("model", "llm", "engine-llm", "coach_model"):
        if val in ("fast", "eco", "low", "3.6", "gemini-3.6-flash-low"):
            cfg["model"] = "gemini-3.6-flash-low"
        elif val in ("balanced", "medium", "3.7", "gemini-3.7-flash-medium"):
            cfg["model"] = "gemini-3.7-flash-medium"
        elif val in ("pro", "deep", "high", "3.8", "gemini-3.8-flash-high"):
            cfg["model"] = "gemini-3.8-flash-high"
        else:
            cfg["model"] = subargs[1]
        save_config(cfg)
        print(f"✅ Real-Time Coach Model impostato su: \033[1;32m{cfg['model']}\033[0m")

    elif key in ("card", "card_model", "cards_model", "audit_model"):
        if val in ("canon", "none", "fast", "0", "zero", "offline"):
            cfg["card_model"] = "canon"
        elif val in ("balanced", "3.7", "gemini-3.7-flash-medium"):
            cfg["card_model"] = "gemini-3.7-flash-medium"
        elif val in ("pro", "deep", "studio", "3.8", "gemini-3.8-flash-high"):
            cfg["card_model"] = "gemini-3.8-flash-high"
        else:
            cfg["card_model"] = subargs[1]
        save_config(cfg)
        print(f"✅ Card & Graphic Production Model impostato su: \033[1;32m{cfg['card_model']}\033[0m")

    elif key in ("tts", "tts_engine", "speech"):
        if val in ("hybrid", "kokoro-edge"):
            cfg["tts_engine"] = "hybrid"
        elif val in ("local", "say", "offline", "mac"):
            cfg["tts_engine"] = "local"
        elif val in ("edge", "cloud", "azure"):
            cfg["tts_engine"] = "edge"
        elif val in ("kokoro", "local-kokoro"):
            cfg["tts_engine"] = "kokoro"
        else:
            cfg["tts_engine"] = val
        save_config(cfg)
        print(f"✅ TTS Engine impostato su: \033[1;32m{cfg['tts_engine']}\033[0m")

    elif key in ("speed", "rate"):
        try:
            sp = float(val)
            if 0.5 <= sp <= 2.0:
                cfg["speed"] = sp
                save_config(cfg)
                print(f"✅ Playback speed impostata su: \033[1;32m{sp}x\033[0m")
            else:
                print("⚠️ Velocità consigliata tra 0.75 e 1.0 (es: 0.75, 0.8, 1.0)")
        except ValueError:
            print("⚠️ Valore numerico non valido per speed.")

    elif key in ("voice", "eng_voice", "english_voice"):
        if "nicole" in val:
            cfg["eng_voice"] = "af_nicole"
        elif "samantha" in val:
            cfg["eng_voice"] = "Samantha"
        elif "adam" in val:
            cfg["eng_voice"] = "am_adam"
        elif "alex" in val:
            cfg["eng_voice"] = "Alex"
        else:
            cfg["eng_voice"] = subargs[1]
        save_config(cfg)
        print(f"✅ English voice impostata su: \033[1;32m{cfg['eng_voice']}\033[0m")

    elif key in ("thai_voice", "thai"):
        if "kanya" in val:
            cfg["thai_voice"] = "Kanya"
        else:
            cfg["thai_voice"] = subargs[1]
        save_config(cfg)
        print(f"✅ Thai voice impostata su: \033[1;32m{cfg['thai_voice']}\033[0m")


    elif key in ("route", "dispatch", "dispatch_mode", "network"):
        if val in ("auto", "cascade"):
            cfg["dispatch_mode"] = "auto"
        elif val in ("dell", "server", "remote"):
            cfg["dispatch_mode"] = "dell"
        elif val in ("local", "mac"):
            cfg["dispatch_mode"] = "local"
        else:
            print("⚠️ Opzioni route valide: auto, dell, local")
            return
        save_config(cfg)
        print(f"✅ Dispatch route impostato su: \033[1;32m{cfg['dispatch_mode']}\033[0m")

    elif key in ("paste", "auto_paste", "auto-paste"):
        cfg["auto_paste"] = val in ("1", "true", "on", "yes", "si")
        save_config(cfg)
        print(f"✅ Auto-paste impostato su: \033[1;32m{cfg['auto_paste']}\033[0m")

    elif key in ("sound", "sound_feedback", "audio_feedback"):
        cfg["sound_feedback"] = val in ("1", "true", "on", "yes", "si")
        save_config(cfg)
        print(f"✅ Audio feedback impostato su: \033[1;32m{cfg['sound_feedback']}\033[0m")

    elif key in ("notify", "notifications"):
        cfg["notifications"] = val in ("1", "true", "on", "yes", "si")
        save_config(cfg)
        print(f"✅ Notifiche desktop impostate su: \033[1;32m{cfg['notifications']}\033[0m")

    else:
        print(f"⚠️ Parametro sconosciuto '{key}'. Esegui 'linguo config' per vedere tutti i parametri disponibili.")
