# 🧠 Linguo

> **Dual English-Thai Voice & Language Coach for Terminal Power Users**  
> *Designed for fast language acquisition, ADHD-friendly active recall, and zero-latency workflow.*

---

## ⚡ Highlights

- **Instantaneous Workflow (<0.5s)**: Fast dictation / text analysis, clipboard copy, and auto-paste (`Cmd+V`) into active apps without blocking.
- **Calm Single-Core Background Audio**: Audio synthesis runs asynchronously in a detached child worker (`nice -n 15`, `torch.set_num_threads(1)`), keeping CPU cool and terminal fluid.
- **Hybrid Neural Speech Engines**:
  - 🇬🇧 **English (100% Local & Offline)**: Powered by [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (24kHz neural voice `af_heart`).
  - 🇹🇭 **Thai**: High-fidelity 48kHz studio audio via **Edge-TTS** (`th-TH-PremwadeeNeural` / `th-TH-NiwatNeural`), with automatic fallback to macOS `Kanya`.
- **ADHD Active Recall & Flashcard TUI (`lb`)**:
  - Curses-based split-view board inside iTerm2.
  - Interactive Flashcard Study Mode (`[f]`) with hidden answers to test active recall before listening.
  - Star / Favorites system (`[s]`) with instant filter toggle (`[Tab]`).
- **Comprehensive Didactic Analysis**:
  - **CEFR Level**: Instant rating (`A1`–`C1`).
  - **Grammar Feedback**: Concise, actionable English grammar explanations.
  - **🚀 Level-Up Alternative**: Advanced B2/C1 phrasing suggestions to level up vocabulary.
  - **🗣️ Phonetics & Pronunciation**: Target tips on word stress, silent letters, and pitfalls for Italian speakers.
  - **🇹🇭 Beginner Thai (2–4 words)**: Ultra-simplified core vocabulary with Paiboon tone marks.
  - **💡 Thai Grammar**: Beginner rules (Subject-Verb-Object, no verb conjugation/tenses, particles, adjectives as verbs).
- **Persistent Memory**: Structured storage in SQLite (`history.db`) and human-readable Markdown (`history.md`).

---

## 🏛️ Architecture & Data Flow

```text
 🎙️ Dictation / CLI Input
            │
            ▼
 ⚡ Antigravity Engine (Flash 3.6 / Gemini)
            │
            ├────────────────────────────────────────┐
            ▼                                        ▼
 📋 Auto-Paste & Terminal Card (<0.5s)    🚀 Detached Worker (nice -n 15, 1 core)
 ├── Instant pbcopy & Cmd+V                          │
 ├── CEFR Level Badge [A2-C1]                        ├─► 🇬🇧 Kokoro-82M (Local Offline)
 ├── Grammar Tip & Level-Up                          │    └── eng_<id>.mp3 (24kHz)
 └── Thai Concept & Breakdown                        │
                                                     └─► 🇹🇭 Edge-TTS / Kanya (Studio)
                                                          └── thai_<id>.mp3 (48kHz)
                                                                     │
                                                                     ▼
                                                          🎧 Replay & Loop ('lr', 'll', 'lb')
```

---

## 📦 Installation

### Prerequisites
- macOS (tested on Monterey and later, Intel & Apple Silicon)
- `ffmpeg` (e.g. via MacPorts or Homebrew)
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)
- [Antigravity CLI](https://antigravity.google) (`agy`)

### Quick Setup

```bash
git clone https://github.com/gptprojectmanager/linguo.git
cd linguo
./install.sh
```

### Python Dependencies (via `uv`)

```bash
uv pip install torch 'numpy<2' soundfile kokoro edge-tts
```

---

## ⌨️ Terminal Usage & Aliases

Add these to your `~/.zshrc`:

```bash
alias lb="linguo board"   # Open ADHD Flashcard TUI Board
alias lr="linguo replay"  # Replay pronunciation of last entry
alias ll="linguo loop"    # Loop pronunciation 3x for memorization
alias lp="linguo popup"   # Toggle recording (start / stop & paste)
alias lv="linguo -v"      # Record from microphone directly
```

### CLI Commands

```bash
# Analyze and synthesize phrase
linguo "I am going to market tomorrow morning"

# Replay last audio
linguo replay
lr

# Replay specific entry by ID
linguo replay 23
lr 23

# Loop playback 3 times
linguo loop 3
ll

# Toggle Star / Favorite
linguo star 24

# Launch interactive board
linguo board
lb

# Configure TTS engine
linguo tts hybrid  # Kokoro English + Edge Thai (Default)
linguo tts kokoro  # 100% Offline English Kokoro + Say Thai
linguo tts edge    # Edge-TTS for both
linguo tts local   # macOS 'say' (Samantha & Kanya)
```

---

## 🧠 ADHD Interactive Board (`lb`)

Launch the board in any iTerm2 tab:

```bash
lb
```

### Keybindings

| Key | Action |
| :--- | :--- |
| `↑` / `↓` or `k` / `j` | Navigate entries |
| `Space` | Play audio / Reveal answer in Flashcard mode |
| `f` | **Toggle Flashcard Mode** (Active Recall challenge) |
| `s` | **Toggle Star (`★`)** on current item |
| `Tab` | **Toggle Filter**: All Items vs. `★ Starred Only` |
| `l` | **Loop 3x**: Plays English ➔ Thai in a 3-repetition cycle |
| `e` | Play English audio only |
| `t` | Play Thai audio only |
| `r` | Refresh entries from database |
| `q` / `ESC` | Exit board |

---

## ⚙️ Configuration

Configuration is located at `~/.local/share/linguo/config.json`:

```json
{
  "hotkey": "<ctrl>+<alt>+<space>",
  "auto_paste": true,
  "sound_feedback": true,
  "tts_engine": "hybrid",
  "eng_voice": "af_heart",
  "thai_voice": "th-TH-PremwadeeNeural",
  "edge_eng_voice": "en-US-JennyNeural",
  "say_eng_voice": "Samantha",
  "say_thai_voice": "Kanya",
  "notifications": true,
  "model": "gemini-3.6-flash-low"
}
```

---

## 📄 License

MIT License. Designed with care for high-focus language acquisition.
