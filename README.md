# Cambridge English Standard

> Automated CEFR formative assessment and cued-recall spaced repetition engine for English language learners, with contrastive L1 Thai phonetic anchoring.

<div align="center">
  <img src="docs/assets/linguo_archetypes_triptych.jpg" alt="Linguo Canonical Arcade Card Archetypes" width="100%" />
  <p><sub>Figure 1: Canonical Linguo formative card archetypes across 3 narrative environments and CEFR topics. Left: <b>Retro Sci-Fi Cyberpunk</b> (Past Simple / The Time Paradox, A2). Center: <b>Fantasy RPG Guild</b> (Verb Patterns / The "To" Toll, B1). Right: <b>Tactical Steampunk</b> (Prepositions & Gerunds / The Gerund Vest, B1). Each card visualizes the grammatical resolution through physical slapstick mechanics.</sub></p>
</div>

---

## Architecture

```mermaid
flowchart LR
    Input["Learner Input<br/>(Speech / Text)"] --> Gate1["Gate 1: CEFR Diagnostic<br/>(A1–C1 / <0.5s)"]
    Gate1 --> Gate2{"Gate 2: Content Decorum"}
    Gate2 -- "Standard" --> Gate3["Gate 3: British Council Audit<br/>(Rule + Paiboon Tones)"]
    Gate2 -- "Sensitive" --> CorrectionOnly["Correction Only<br/>(Card Suppressed)"]
    Gate3 --> Deck["Active Recall Deck<br/>(Single [ ? ] Blank)"]
    Deck --> TTS["Speech Synthesis<br/>(0.80x / 140 wpm)"]
```

---

## Pedagogical Validation Gates

* **Gate 1 (Real-Time Diagnostic)**: Evaluates input against CEFR levels (A1–C1) within $<0.5\text{s}$ using Pydantic v2 schemas.
* **Gate 2 (Decorum & Ethics)**: Deterministic filter. Educational corrections are returned; permanent card minting is suppressed for sensitive topics (`SENSITIVE_NO_CARD`).
* **Gate 3 (Formative Audit)**: Synthesizes recurrent structural gaps into canonical British Council grammar rules, verifies 5-tone Paiboon notation, and commits immutable challenge cards.

---

## Core Specifications

* **Cued-Recall Testing**: Single targeted blank `[  ?  ]` to enforce active retrieval over passive recognition.
* **Starter Deck (Cold-Start Free)**: 15 canonical CEFR A1–B2 cards pre-loaded on install across high-frequency error categories (articles, aspect, prepositions, conditionals).
* **Contrastive Scaffolding**: Direct transfer mapping for L1 Thai (zero-article interference, unmarked aspect, verb complementation).
* **Dual Deck Export**: Native `.apkg` packages with 16-bit arcade CSS styling and TSV tables for Anki, AnkiMobile, and Quizlet.
* **Calibrated Acoustic Speed**: 140 wpm ($175\text{ wpm} \times 0.80$) for perceptual phonemic discrimination.
* **Mastery Lifecycle**: Items graduate to Mastered after 3 consecutive clean usages; recidivism automatically reactivates the card.
* **Enterprise Telemetry**: OpenMetrics endpoint (`GET /metrics`), W3C distributed tracing (`X-Trace-Id`), systemd service unit, Cloudflare ingress, and NDJSON structured logging.

---

## Quickstart

```bash
# 1. Clone and install
git clone https://github.com/gptprojectmanager/linguo.git
cd linguo && ./install.sh

# 2. Run diagnostics and unified test suite (11/11 phases passing)
./tests/test_all.sh

# 3. Assess a phrase
linguo "I go to market yesterday"

# 4. Export active deck (Native Anki .apkg + TSV)
linguo export            # Generates cards_anki_export.apkg & cards_anki_export.tsv
linguo export apkg       # Native Anki package with 16-bit arcade styling
```

---

## License

MIT License. Open CALL reference implementation.
