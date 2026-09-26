# 🧠 Linguo

> **Dual English-Thai Voice & Language Coach with 16-bit MTG Arcade HUD**  
> *Designed for high-focus language acquisition, ADHD-friendly active recall, and zero-latency workflow.*

---

## ⚡ Highlights

- **Instantaneous Dictation & Coach (<0.5s)**: Fast speech analysis, clipboard copy, and auto-paste (`Cmd+V`) into active apps without blocking.
- **16-bit MTG Trading Card Engine**: Clusters recurring speech gaps into collectible Magic: The Gathering-style puzzle cards (Active Recall Challenge on the front, Cambridge solution + British Council rule + arcade gag on the back).
- **Native Rust Metal 60fps HUD (`dash-gui`)**:
  - Pure Rust immediate-mode desktop window (`eframe` / `wgpu`).
  - True 16-bit arcade aesthetics with TrueType Ayuthaya Thai font support (`/System/Library/Fonts/Supplemental/Ayuthaya.ttf`).
  - Always-on-Top pinning mode (`[P]`), 0% CPU at idle, ~15 MB RAM footprint.
- **ADHD Spaced Repetition & Algorithmic Auto-Mastery**:
  - Automatically archives cards (`is_mastered = 1`) after a streak of 3 consecutive clean usages in subsequent real speech.
  - **Recidivism Detection**: Automatically reactivates mastered cards if errors re-occur weeks later.
- **Calm Single-Core Background Audio**:
  - 🇬🇧 **English (100% Local & Offline)**: Powered by [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (24kHz neural voice `af_nicole` @ 0.8x didactic pace).
  - 🇹🇭 **Thai Studio Pipeline**: Edge-TTS studio quality (`th-TH-PremwadeeNeural` @ 0.8x) backed by a 75-brick local offline cache and native macOS `say -v Kanya` fallback.
- **Pydantic v2 Rust-Core Schema Validation**:
  - Sub-millisecond schema parsing with fuzzy auto-healing of categories.
- **ADHD Active Recall & Flashcard TUI (`lb`)**:
  - Curses-based split-view board inside any terminal.
- **Anki Mobile Integration**: One-click TSV deck export with HTML formatting for Anki Desktop and AnkiMobile (`linguo --export`).

---

## 🏛️ Architecture & Data Flow

```text
 🎙️ Dictation / CLI Input
            │
            ▼
 ⚡ Antigravity Engine (Flash 3.6 / Gemini)
            │
            ├────────────────────────────────────────┬────────────────────────────────────────┐
            ▼                                        ▼                                        ▼
 📋 Auto-Paste (<0.5s)                     🗃️ SQLite WAL (history.db)               🚀 Background Audio Worker
 ├── Instant pbcopy & Cmd+V                ├── history table                        │   (nice -n 15, 1 core)
 ├── CEFR Level Badge [A1-C1]              ├── cards table (MTG deck)               ├─► 🇬🇧 Kokoro-82M (0.8x)
 ├── Grammar Tip & Level-Up                └── card_archetypes table                │    └── eng_<id>.mp3
 └── Pydantic v2 Rust Schema                                                        └─► 🇹🇭 Edge-TTS / Cache (0.8x)
                                                                                         └── thai_<id>.mp3
                                                     │
                             ┌───────────────────────┴───────────────────────┐
                             ▼                                               ▼
               🕹️ Native Rust HUD (dash-gui)                   🧠 ADHD Curses TUI (lb)
               ├── 16-bit MTG Challenge & Flip                 ├── Split-view history
               ├── Metal GPU Accelerated (60fps)               ├── Flashcard mode [f]
               ├── Always-on-Top Pinning [P]                   └── Audio loop 3x [l]
               └── Local Thai & English Replay
```

---

## 📦 Installation

### Prerequisites
- macOS (Monterey or later, Intel & Apple Silicon)
- `ffmpeg` (e.g. via MacPorts or Homebrew)
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)
- [Rust](https://rustup.rs) (for compiling the native Metal HUD)

### One-Line Setup

```bash
git clone https://github.com/gptprojectmanager/linguo.git
cd linguo
./install.sh
```

`install.sh` automatically configures directories, copies binaries, synchronizes agent prompts, installs Python dependencies via `uv`, and compiles the native Rust HUD `dash-gui` with codesigning.

---

## 🕹️ Native Rust 16-bit MTG HUD (`dash-gui`)

Launch the floating HUD:

```bash
linguo-gui
# or via CLI:
linguo --gui
```

### HUD Controls & Keybindings

| Key | Action | Description |
| :--- | :--- | :--- |
| `Space` | **Flip Card** | Toggle between Front (Challenge) and Back (Solution + Gag) |
| `P` | **Pin Window** | Toggle Always-on-Top floating mode |
| `A` / `←` | **Previous Card** | Navigate to previous card in deck |
| `D` / `→` | **Next Card** | Navigate to next card in deck |
| `E` | **Play English** | Listen to British Council solution (Kokoro `af_nicole` 0.8x) |
| `T` / `R` | **Play Thai** | Listen to Thai survival brick (Edge-TTS `Premwadee` 0.8x) |
| `M` | **Master Card** | Toggle card as mastered / archived |
| `F5` | **Reload Deck** | Reload cards from SQLite database |

---

## ⌨️ CLI Commands & Aliases

Add these aliases to your `~/.zshrc`:

```bash
alias lg="linguo --gui"   # Launch native 16-bit MTG HUD
alias lb="linguo board"   # Open ADHD Flashcard CUI/TUI Board
alias lr="linguo replay"  # Replay audio pronunciation of last entry
alias ll="linguo loop"    # Loop pronunciation 3x for memorization
alias lv="linguo -v"      # Record from microphone directly
```

### Full CLI Command Reference

```bash
# 1. Analyze and synthesize phrase
linguo "I am going to market tomorrow morning"

# 2. British Council Gap Audit & MTG Card Minting
linguo --audit

# 3. View active MTG cards in terminal
linguo --cards
linguo --flip 1           # Reveal card solution & British Council rule
linguo --master 1         # Mark card as mastered

# 4. Launch Native Rust GUI HUD
linguo --gui              # or: linguo-gui

# 5. Launch Terminal Curses TUI Board
linguo --board            # or: lb

# 6. Replay & Loop Audio
linguo replay             # or: lr
linguo replay 5           # replay specific entry #5
linguo loop 3             # or: ll (3-repetition cycle)

# 7. System Diagnostics & Permission Check
linguo --doctor

# 8. Pre-cache 75 Thai Survival Audio Bricks (100% Offline)
linguo --preseed

# 9. Export Deck to Anki TSV
linguo --export
```

---

## 🧪 Automated Test Suite

Run the full end-to-end test suite:

```bash
./tests/test_all.sh
```

Verifies:
- Python syntax compilation
- Pydantic v2 schema validator and auto-healing
- SQLite WAL mode and database tables (`history`, `cards`, `card_archetypes`)
- System diagnostics (`linguo --doctor`)
- British Council audit engine
- Anki TSV export generator
- Native Rust `dash-gui` Metal executable

---

## ⚙️ Configuration

Configuration is located at `~/.local/share/linguo/config.json`:

```json
{
  "hotkey": "<ctrl>+<alt>+<space>",
  "auto_paste": true,
  "sound_feedback": true,
  "tts_engine": "hybrid",
  "eng_voice": "af_nicole",
  "thai_voice": "th-TH-PremwadeeNeural",
  "speed": 0.8,
  "say_eng_voice": "Samantha",
  "say_thai_voice": "Kanya",
  "notifications": true,
  "model": "gemini-3.6-flash-low"
}
```

---

## 📄 License

MIT License. Crafted with care for zero-friction language mastery.
