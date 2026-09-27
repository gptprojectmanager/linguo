# 📝 Changelog

All notable changes to **Linguo** are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-09-27

### 🎴 Starter Deck, Native APKG, Modular Architecture & Operational Stack
- **15-Card CEFR A1–B2 Starter Deck**:
  - Solves the cold-start problem (`0 cards` on fresh install) by pre-seeding 15 canonical Cambridge/British Council error archetypes directly into SQLite WAL `cards` table during `init_db()`.
  - Covers articles, aspect, prepositions, conditionals, collocations, and quantifiers with single-blank active recall puzzles `[  ?  ]`.
- **Native Anki Package Exporter (`.apkg`)**:
  - Implemented pure-Python `.apkg` compiler in `linguo/pedagogy/export.py` using standard library `sqlite3` and `zipfile` (zero heavy external dependencies).
  - Embeds custom 16-bit dark arcade CSS styling (`#0d1117`, gold accents, neon cyan highlights, glowing answer boxes) for Anki Desktop and AnkiMobile.
  - CLI commands: `linguo export` (both TSV and APKG), `linguo export apkg`, `linguo export tsv`.
- **Complete Modular Package Refactoring**:
  - Decomposed the monolithic codebase into structured Python packages:
    - `linguo/core/`: `config.py`, `db.py`, `models.py`, `safety.py`, `telemetry.py`, `starter_deck.py`.
    - `linguo/audio/`: `engine.py` (Kokoro-82M 2-thread local CPU synthesis + Edge-TTS).
    - `linguo/pedagogy/`: `export.py` (TSV and APKG generation).
    - `linguo/platform/`: `macos.py` (pbcopy, AppleScript paste, sounds, notifications).
  - `bin/linguo` preserved as a backwards-compatible wrapper maintaining 100% test compatibility.
- **Dell 7670 Operational Deployment Stack**:
  - `config/linguo-server.service`: Production systemd service unit running Uvicorn with 2 workers, resource bounds (4G RAM, 300% CPU), and journald logging.
  - `config/cloudflare_tunnel.yml`: Cloudflare Tunnel ingress configuration routing `linguo.princyx.xyz` to port 8765.
  - `config/prometheus_scrape.yml`: Prometheus scrape configuration for `/metrics` with Bearer auth token.
  - `scripts/deploy_dell.sh`: Fully automated deployment script to initialize venv, configure systemd, and run health probes.
- **Isolated E2E Sandbox Test Harness**:
  - `tests/test_e2e_isolated.py`: Spawns ephemeral server on port 18765, runs 10 lifecycle checks in isolated temp directories, and proves zero host database contamination.
  - Unified test suite (`./tests/test_all.sh`) expanded to 11/11 phases, all passing.
- **Visual Showcase Redesign**:
  - Replaced temporary card graphics with a panoramic 16:9 triptych (`docs/assets/linguo_archetypes_triptych.jpg`) showcasing the 3 narrative archetypes (Cyberpunk Past Simple, Fantasy RPG Verb Patterns, Tactical Steampunk Gerunds) with slapstick physical comedy and original cartoon characters.

---

## [0.3.3] - 2026-09-26

### ⚙️ Interactive Configuration Matrix (GUI & CLI)
- **Settings & Configuration Modal (`⚙️ Config` / `[C]`)**:
  - Interactive configuration matrix in `dash-gui` with discrete options across 7 operational domains:
    1. **Real-Time Coach Model**: `gemini-3.6-flash-low` (⚡ Fast 3.6 Low, default), `gemini-3.7-flash-medium` (⚖️ Balanced 3.7), `gemini-3.8-flash-high` (🧠 Deep 3.8 Pro).
    2. **Card & Graphic Production (Token Gate)**: `canon` (⚡ Canonico 0 Token, instant SQLite archetypes), `gemini-3.7-flash-medium` (⚖️ Balanced 3.7), `gemini-3.8-flash-high` (🔬 Studio 3.8 High, default).
    3. **TTS Speech Engine**: `hybrid` (Kokoro + Edge-TTS, default), `local` (macOS offline Say), `edge` (Azure Cloud).
    4. **Playback Speed**: `0.75x` (Lenta), `0.80x` (Didattica, default), `1.00x` (Naturale).
    5. **English Voice & Quality (Dropdown)**:
       - 👩 **Nicole**: `af_nicole` [Studio Neural 24kHz • Kokoro British Female, default]
       - 👩 **Samantha**: `Samantha` [macOS Built-in • Apple System American Female]
       - 👨 **Adam**: `am_adam` [Studio Neural 24kHz • Kokoro American Male]
       - 👨 **Alex**: `Alex` [macOS Built-in • Apple System American Male]
    6. **Network Routing Dispatch**: `auto` (Cascade: WireGuard -> Cloudflare -> Local Mac, default), `dell` (Force Server), `local` (Force Mac).
    7. **Client Automation Toggles**: `auto_paste` (Cmd+V), `sound_feedback`, `notifications`.
  - Immediate atomic persistence to `~/.local/share/linguo/config.json`.
  - Factory reset button ("Ripristina Predefiniti") restoring canonical defaults.
- **Unified CLI Configuration Engine (`linguo config`)**:
  - Terminal matrix inspection: `linguo config`.
  - Subcommands: `linguo config model <fast|balanced|pro>`, `linguo config card <canon|balanced|studio>`, `linguo config voice <nicole|samantha|adam|alex>`, `linguo config speed <0.75|0.8|1.0>`, `linguo config route <auto|dell|local>`, `linguo config reset`.
- **Menu Bar Context Menu Integration**:
  - Added "⚙️ Impostazioni Config..." item to the right-click menu of the 🎙️ menu bar accessory.

---

## [0.3.2] - 2026-09-26

### 🎙️ macOS Menu Bar LaunchAgent & 3-Gate Quality Pipeline
- **macOS Menu Bar LaunchAgent (`com.linguo.bar.plist`)**:
  - Automatically loads and runs the 🎙️ menu bar accessory on macOS login.
  - Native contextual menu on right click: Start/Stop voice recording, Open Metal HUD, Run Doctor diagnostics, and Clean Quit.
  - Thread-safe UI updates and zero-terminal lifecycle management (`linguo --install-bar`, `linguo --uninstall-bar`, `linguo --status-bar`).
  - Added as Pillar 7 in `linguo --doctor`.
- **Gate 2: Content Moderation & Sensitive Filter**:
  - Fast deterministic keyword & phrase filter for sensitive/NSFW topics (weapons, violence, illicit drugs, sexual content, hate speech).
  - Pedagogical corrections and Thai translations are preserved, but tagged with `SENSITIVE_NO_CARD` to strictly prevent gamified MTG card minting.
- **Gate 3: Deep Pedagogical Audit via Gemini 3.8 Flash High**:
  - Upgraded recurring gap auditing (`linguo --audit`) to invoke `gemini-3.8-flash-high` with high reasoning effort.
  - Validates British Council grammar accuracy and Paiboon tonal marks (Low, Mid, High, Falling, Rising).
  - Enforces deterministic slot-filling into 3 immutable canonical archetypes (Tactical Military Arcade, Retro Sci-Fi Cyberpunk, Fantasy RPG Guild) to eliminate stylistic drift over time.
- **Test Suite Expansion**:
  - Automated test suite upgraded to 9/9 automated tests verifying Pydantic v2 schemas, WAL SQLite, Gate 2 safety filters, and LaunchAgent status.

---

## [0.3.1] - 2026-09-26

### 🌐 Remote Backend & In-App Practice
- **Remote Coach API on Dell 7670 (`scripts/linguo_server.py`)**:
  - FastAPI server with Bearer token authentication, running as a systemd service (`linguo-server.service`).
  - Pre-configured agent `linguo-fast` with zero tools (`tools: []`) and minimal token consumption on `gemini-3.6-flash-low` with low effort.
- **Dual Remote/Local Dispatch in `dash-gui`**:
  - Automatically queries remote backend via curl if `remote_url` is configured or `LINGUO_REMOTE_URL` is set, with graceful fallback to local CLI.
  - Automatically initializes local SQLite schema (`history`, `cards`) on virgin Macs.
  - Speaks corrected English via `Samantha` and beginner Thai via `Kanya` without needing Python or external libraries.
- **In-App Practice & Live Coach Bar**:
  - Interactive input field and `⚡ Coach Me` button in the Metal HUD header.

---

## [0.3.0] - 2026-09-26

### 🚀 Highlights
- **macOS Drag & Drop DMG Installer (`Linguo-0.3.0.dmg`)**:
  - Full native 60fps Metal arcade HUD (`dash-gui`) packaged as a standalone 4.0 MB DMG with `/Applications` symlink.
  - Zero terminal knowledge required for non-technical users.
- **6 Fundamental Diagnostic Pillars (`linguo --doctor`)**:
  - Reorganized diagnostic engine to verify Core Engine & DB, Audio Pipeline (3-tier), macOS TCC & Keystrokes, Rust Metal HUD, Active Recall Deck (MTG), and Logging/Tracing.
- **Fine-Grained Latency Tracing (`linguo --trace`)**:
  - Added ASCII bar chart profiling breakdown across pipeline stages (SQLite WAL, Clipboard, LLM Inference, Pydantic v2, DB Commit, Audio Dispatch).
- **Parsimonious 30-Day Logging (`linguo --logs`)**:
  - Low-overhead daily rotating log engine with automatic purge of files older than 30 days (`~/.local/share/linguo/logs/`).
- **Security & Secret Gates**:
  - Added `.git/hooks/pre-commit` and `scripts/check_secrets.sh` to block accidental commits of API keys or private tokens.

### 🎧 Audio & Engine
- Kokoro-82M 24kHz neural voice (`af_nicole` @ 0.8x) running on CPU on a single core (`torch.set_num_threads(1)`).
- Edge-TTS studio quality (`th-TH-PremwadeeNeural` @ 0.8x) with 75 pre-cached survival Thai audio bricks.
- Graceful degradation to macOS native `Samantha` and `Kanya` system speech.

---

## [0.2.0] - 2026-09-25

### 🎮 Features
- **16-bit MTG Trading Card Engine**: Clusters recurring speech gaps into collectible retro cards with Active Recall challenges, British Council rules, and arcade gags.
- **Always-on-Top Floating HUD**: Added shortcut `[P]` and header button in `dash-gui` to pin the HUD above active windows.
- **Apple Ayuthaya TrueType Font**: Native Thai script rendering in Rust/Metal UI.
- **Dynamic Archetypes Table**: `card_archetypes` SQLite table allowing live extension of card templates.

---

## [0.1.0] - 2026-09-24

### ⚡ Initial Release
- Instant dictation and clipboard auto-paste (<0.5s).
- Pydantic v2 Rust-core schema validation.
- SQLite WAL concurrency mode.
- Curses ADHD interactive terminal board (`lb`).
- Anki TSV export generator (`linguo --export`).
