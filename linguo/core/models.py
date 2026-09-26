"""
Linguo Pydantic v2 Models & Schema Validation
Sanitizes LLM hallucinated categories into British Council standards.
"""

import re
import json
import time
from typing import Literal
from .safety import detect_sensitive_content
from .telemetry import log_event

try:
    import pydantic
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


if PYDANTIC_AVAILABLE:
    class LinguoAnalysis(BaseModel):
        transcribed_english: str = ""
        is_correct: bool = True
        error_category: Literal[
            "ARTICLES", "PREPOSITIONS", "VERB_PATTERNS", "TENSES",
            "WORD_ORDER", "AGREEMENT", "COLLOCATIONS", "SINCE_FOR",
            "MAKE_DO", "MUCH_MANY", "SAY_TELL", "PARTICIPLE_ADJECTIVES",
            "STILL_ALREADY", "FIRST_CONDITIONAL", "USED_TO",
            "DEPENDENT_PREPOSITIONS", "FEW_A_FEW", "SENSITIVE_NO_CARD", "NONE"
        ] = "NONE"
        english_level: str = "B1"
        corrected_english: str = ""
        grammar_tip: str = ""
        english_better_alternative: str = ""
        pronunciation_tip: str = ""
        thai_concise_script: str = ""
        thai_phonetic_western: str = ""
        thai_breakdown: str = ""
        thai_grammar_tip: str = ""

        @field_validator("error_category", mode="before")
        @classmethod
        def sanitize_error_category(cls, v):
            """Auto-heals LLM hallucinations into strict standard categories."""
            if not v or not isinstance(v, str):
                return "NONE"
            v_upper = v.upper().strip()
            allowed = {
                "ARTICLES", "PREPOSITIONS", "VERB_PATTERNS", "TENSES",
                "WORD_ORDER", "AGREEMENT", "COLLOCATIONS", "SINCE_FOR",
                "MAKE_DO", "MUCH_MANY", "SAY_TELL", "PARTICIPLE_ADJECTIVES",
                "STILL_ALREADY", "FIRST_CONDITIONAL", "USED_TO",
                "DEPENDENT_PREPOSITIONS", "FEW_A_FEW", "SENSITIVE_NO_CARD", "NONE"
            }
            if v_upper in allowed:
                return v_upper
            if "SENSITIVE" in v_upper or "NSFW" in v_upper or "SAFETY" in v_upper:
                return "SENSITIVE_NO_CARD"
            if "ARTICLE" in v_upper:
                return "ARTICLES"
            if "SINCE" in v_upper or "FOR" in v_upper:
                return "SINCE_FOR"
            if "MAKE" in v_upper or "DO" in v_upper:
                return "MAKE_DO"
            if "MUCH" in v_upper or "MANY" in v_upper:
                return "MUCH_MANY"
            if "TELL" in v_upper or "SAY" in v_upper:
                return "SAY_TELL"
            if "PARTICIPLE" in v_upper or "BORED" in v_upper or "BORING" in v_upper:
                return "PARTICIPLE_ADJECTIVES"
            if "STILL" in v_upper or "ALREADY" in v_upper:
                return "STILL_ALREADY"
            if "CONDITION" in v_upper or "IF" in v_upper:
                return "FIRST_CONDITIONAL"
            if "USED TO" in v_upper:
                return "USED_TO"
            if "DEPEND" in v_upper:
                return "DEPENDENT_PREPOSITIONS"
            if "FEW" in v_upper:
                return "FEW_A_FEW"
            if "PREP" in v_upper:
                return "PREPOSITIONS"
            if "VERB" in v_upper or "INFINITIVE" in v_upper:
                return "VERB_PATTERNS"
            if "TENSE" in v_upper or "PAST" in v_upper:
                return "TENSES"
            if "AGREE" in v_upper or "SINGULAR" in v_upper:
                return "AGREEMENT"
            if "ORDER" in v_upper:
                return "WORD_ORDER"
            if "COLLOCAT" in v_upper:
                return "COLLOCATIONS"
            return "NONE"

        @field_validator("is_correct", mode="before")
        @classmethod
        def sanitize_is_correct(cls, v):
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.strip().lower() in ("true", "1", "yes")
            return bool(v)
else:
    class LinguoAnalysis:
        pass


def parse_and_validate_analysis(raw_text: str, fallback_input: str = "") -> dict:
    """Extracts JSON and validates through Pydantic v2 with deterministic fallbacks."""
    t0 = time.perf_counter()
    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    json_str = json_match.group(0) if json_match else raw_text.strip()

    result = None
    if PYDANTIC_AVAILABLE:
        try:
            model = LinguoAnalysis.model_validate_json(json_str)
            if not model.transcribed_english and fallback_input:
                model.transcribed_english = fallback_input
            if not model.corrected_english:
                model.corrected_english = model.transcribed_english
            result = model.model_dump()
        except Exception:
            try:
                parsed = json.loads(json_str)
                model = LinguoAnalysis.model_validate(parsed)
                if not model.transcribed_english and fallback_input:
                    model.transcribed_english = fallback_input
                if not model.corrected_english:
                    model.corrected_english = model.transcribed_english
                result = model.model_dump()
            except Exception:
                pass

    if not result:
        # Emergency heuristic fallback
        result = {
            "transcribed_english": fallback_input,
            "is_correct": True,
            "error_category": "NONE",
            "english_level": "B1",
            "corrected_english": fallback_input,
            "grammar_tip": "",
            "english_better_alternative": "",
            "pronunciation_tip": "",
            "thai_concise_script": "",
            "thai_phonetic_western": "",
            "thai_breakdown": "",
            "thai_grammar_tip": ""
        }

    # Gate 2 Check: Overwrite error_category if sensitive content is detected
    combined = f"{result['transcribed_english']} {result['corrected_english']}"
    if detect_sensitive_content(combined):
        result["error_category"] = "SENSITIVE_NO_CARD"

    dt_ms = (time.perf_counter() - t0) * 1000.0
    log_event("DEBUG", "SCHEMA", "Pydantic parsing complete", {"latency_ms": round(dt_ms, 2)})
    return result
