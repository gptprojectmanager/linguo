"""
Linguo Safety & Content Moderation Gate (Gate 2)
Fast deterministic filter to reject violent, NSFW, or illegal substance terms
and prevent accidental flashcard minting of inappropriate content.
"""

import re

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
