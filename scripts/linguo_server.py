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

app = FastAPI(
    title="Linguo Remote Coach API",
    version="0.3.0",
    description="AI English & Thai Language Acquisition Backend on Dell 7670"
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
    
    analysis = AnalysisData(
        transcribed_english=parsed.get("transcribed_english", phrase),
        is_correct=bool(parsed.get("is_correct", True)),
        error_category=parsed.get("error_category", "NONE"),
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
