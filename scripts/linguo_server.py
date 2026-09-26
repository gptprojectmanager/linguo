#!/usr/bin/env python3
"""
Linguo Remote Coach API Server (FastAPI + AGY on Dell 7670)
Exposes /coach and /health endpoints with Bearer token authentication
for zero-terminal remote clients (macOS dash-gui in Portugal).
"""

import os
import re
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Security Token (default fallback or environment)
API_SECRET_TOKEN = os.environ.get("LINGUO_API_TOKEN", "linguo-secret-key-2026-linguo-coach")

SENSITIVE_KEYWORDS = {
    # Weapons / Violence
    "gun", "guns", "pistol", "rifle", "shoot", "shooting", "shot", "kill", "killing", "murder",
    "knife", "knives", "stab", "stabbing", "bomb", "bombs", "explosive", "explosives",
    "terrorist", "terrorism", "weapon", "weapons", "assault", "grenade", "bullet", "ammunition",
    # Drugs / Illegal Substances
    "cocaine", "heroin", "meth", "methamphetamine", "weed", "cannabis", "marijuana",
    "narcotic", "narcotics", "overdose", "cartel", "drug deal", "drug dealer", "ecstasy", "fentanyl",
    # Explicit / NSFW
    "sex", "sexual", "porn", "pornography", "naked", "nude", "penis", "vagina", "boobs", "dick",
    "pussy", "prostitute", "prostitution", "escort", "blowjob", "fuck", "fucking", "orgasm"
}

def detect_sensitive_content(text: str) -> bool:
    """Fast deterministic gate (Gate 2) to identify NSFW, violent, or sensitive terms."""
    if not text:
        return False
    lowered = text.lower()
    for phrase in ["drug deal", "drug dealer", "blow job", "have sex", "kill someone"]:
        if phrase in lowered:
            return True
    words = set(re.findall(r"\b[a-z]+\b", lowered))
    return bool(words & SENSITIVE_KEYWORDS)

app = FastAPI(
    title="Linguo Remote Coach API",
    version="0.3.1",
    description="AI English & Thai Language Acquisition Backend on Dell 7670 with 3-Gate Pedagogical Review"
)

# CORS middleware to allow cross-origin requests from GUI clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CoachRequest(BaseModel):
    phrase: str = Field(..., min_length=1, description="English phrase to analyze")
    mode: Optional[str] = Field("fast", description="Analysis profile: 'fast' (zero-tools) or 'full'")

class AuditSample(BaseModel):
    original: str
    corrected: str
    tip: Optional[str] = ""

class AuditRequest(BaseModel):
    category: str
    samples: list[AuditSample] = []

class CardSlotData(BaseModel):
    card_title: str
    card_type: str = "Arcade Encounter • Grammar"
    cefr_level: str = "B1"
    front_challenge: str
    back_solution: str
    british_council_rule: str
    gag_quote: str
    thai_script: str
    thai_phonetic: str
    thai_tones: str
    thai_breakdown: str
    sprite_name: str = "arcade_badge"

class AuditResponse(BaseModel):
    status: str
    timing_ms: float
    model: str
    card: CardSlotData

class AnalysisData(BaseModel):
    transcribed_english: str
    is_correct: bool
    error_category: str = "NONE"
    english_level: str = "B1"
    corrected_english: str
    grammar_tip: str
    english_better_alternative: Optional[str] = ""
    pronunciation_tip: Optional[str] = ""
    thai_concise_script: str = ""
    thai_phonetic_western: str = ""
    thai_breakdown: str = ""
    thai_grammar_tip: str = ""

class CoachResponse(BaseModel):
    status: str
    timing_ms: float
    analysis: AnalysisData

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    prefix = "Bearer "
    if not authorization.startswith(prefix) or authorization[len(prefix):].strip() != API_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or unauthorized API token")
    return True

def clean_json_text(raw: str) -> str:
    cleaned = raw.strip()
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
    if match:
        return match.group(1).strip()
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace:last_brace+1].strip()
    return cleaned

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "linguo-remote-backend",
        "host": "sam7670",
        "engine": "gemini-3.6-flash-low",
        "agent": "linguo-fast"
    }

@app.post("/coach", response_model=CoachResponse)
def coach_phrase(req: CoachRequest, authenticated: bool = Depends(verify_token)):
    t0 = time.perf_counter()
    phrase = req.phrase.strip()
    if not phrase:
        raise HTTPException(status_code=400, detail="Phrase cannot be empty")

    agy_bin = Path.home() / ".local" / "bin" / "agy"
    if not agy_bin.exists():
        agy_bin = Path("agy")

    workspace = Path.home() / ".local" / "share" / "linguo" / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(agy_bin),
        "--agent", "linguo-fast",
        "--model", "gemini-3.6-flash-low",
        "--dangerously-skip-permissions",
        "--disable-slash-commands",
        "--effort", "low",
        "--output-format", "json",
        "-p", f'Analyze: """{phrase}"""'
    ]

    try:
        res = subprocess.run(
            cmd,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=30.0,
            check=True
        )
        outer = json.loads(res.stdout)
        raw_response = outer.get("response", "").strip()
        cleaned = clean_json_text(raw_response)
        parsed = json.loads(cleaned)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="AGY inference timed out (>30s)")
    except subprocess.CalledProcessError as e:
        err = e.stderr or e.stdout
        raise HTTPException(status_code=500, detail=f"AGY process error: {err[:200]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON parsing error: {e}")

    dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    
    category = parsed.get("error_category", "NONE")
    raw_to_check = f"{phrase} {parsed.get('transcribed_english', '')} {parsed.get('corrected_english', '')}"
    if detect_sensitive_content(raw_to_check):
        category = "SENSITIVE_NO_CARD"

    analysis = AnalysisData(
        transcribed_english=parsed.get("transcribed_english", phrase),
        is_correct=bool(parsed.get("is_correct", True)),
        error_category=category,
        english_level=parsed.get("english_level", "B1"),
        corrected_english=parsed.get("corrected_english", phrase),
        grammar_tip=parsed.get("grammar_tip", ""),
        english_better_alternative=parsed.get("english_better_alternative", ""),
        pronunciation_tip=parsed.get("pronunciation_tip", ""),
        thai_concise_script=parsed.get("thai_concise_script", ""),
        thai_phonetic_western=parsed.get("thai_phonetic_western", ""),
        thai_breakdown=parsed.get("thai_breakdown", ""),
        thai_grammar_tip=parsed.get("thai_grammar_tip", "")
    )

    return CoachResponse(status="success", timing_ms=dt_ms, analysis=analysis)

@app.post("/audit", response_model=AuditResponse)
def audit_cluster(req: AuditRequest, authenticated: bool = Depends(verify_token)):
    t0 = time.perf_counter()
    category = req.category.strip().upper()
    if category in ("SENSITIVE_NO_CARD", "NONE", ""):
        raise HTTPException(status_code=400, detail="Cannot audit or mint cards for sensitive or empty categories")

    agy_bin = Path.home() / ".local" / "bin" / "agy"
    if not agy_bin.exists():
        agy_bin = Path("agy")

    workspace = Path.home() / ".local" / "share" / "linguo" / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    samples_data = [{"original": s.original, "corrected": s.corrected, "tip": s.tip} for s in req.samples[:5]]
    prompt = f"""You are a British Council Senior Grammar Examiner and Thai Paiboon Phonetician.
Conduct a rigorous pedagogical audit on this recurring error cluster:
Category: {category}
Error Samples: {json.dumps(samples_data, ensure_ascii=False)}

TASKS:
1. Formulate a precise, canonical British Council grammar rule for this gap (1 concise sentence).
2. Create an unambiguous fill-in-the-blank challenge puzzle with exactly ONE [  ?  ] blank.
3. Select an essential, natural 2-4 word Thai beginner concept with accurate Paiboon tone marks (â=falling, á=high, à=low, ǎ=rising, plain=mid).
4. Strictly ground the style into ONE of these 3 canonical archetypes:
   - 'Tactical Military Arcade' (persona: Drill Sergeant, e.g. "NO 'THE', NO ENTRY! Stamp approved, soldier!")
   - 'Retro Sci-Fi Cyberpunk' (persona: Time Traveler, e.g. "TIME PARADOX! Drop present tense before the continuum breaks!")
   - 'Fantasy RPG Guild' (persona: Guild Master, e.g. "ACCESS DENIED! Insert 'TO' token into the machine!")

Output MUST be a single valid JSON object only with exactly these keys:
{{
  "card_title": "UPPERCASE TITLE (2-4 words, e.g. THE MARKET STAMP)",
  "card_type": "Arcade Encounter • Grammar",
  "cefr_level": "A2 or B1 or B2",
  "front_challenge": "Sentence with exactly one [  ?  ] blank",
  "back_solution": "Full correct sentence with target word in CAPITAL LETTERS",
  "british_council_rule": "Rigorous British Council grammar rule (1 sentence)",
  "gag_quote": "Humorous, punchy 1-sentence in-character quote matching the chosen archetype",
  "thai_script": "2-4 word simplified beginner Thai script",
  "thai_phonetic": "Latin Paiboon phonetics",
  "thai_tones": "Explicit tone sequence (e.g. 'M / L' or 'L / M / H')",
  "thai_breakdown": "word1 (tone) = meaning | word2 (tone) = meaning",
  "sprite_name": "market_stamp or to_toll or gerund_vest or time_paradox or lone_s_gun"
}}
"""

    cmd = [
        str(agy_bin),
        "--model", "gemini-3.8-flash-high",
        "--effort", "high",
        "--dangerously-skip-permissions",
        "--disable-slash-commands",
        "--output-format", "json",
        "-p", prompt
    ]

    try:
        res = subprocess.run(cmd, cwd=str(workspace), capture_output=True, text=True, timeout=35.0, check=True)
        outer = json.loads(res.stdout)
        raw = outer.get("response", "").strip()
        cleaned = clean_json_text(raw)
        parsed = json.loads(cleaned)
        card = CardSlotData(**parsed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flash 3.8 audit failed: {e}")

    dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return AuditResponse(status="success", timing_ms=dt_ms, model="gemini-3.8-flash-high", card=card)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
