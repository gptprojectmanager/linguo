"""
Linguo Core Module
Configuration, Database, Schema Validation, Safety Moderation, Telemetry.
"""
from .config import DATA_DIR, AUDIO_DIR, DB_PATH, LOG_PATH, CONFIG_PATH, WORKSPACE_DIR, LOGS_DIR, DEFAULT_CONFIG, load_config, save_config, show_config_cli
from .safety import SENSITIVE_KEYWORDS, detect_sensitive_content
from .models import LinguoAnalysis, parse_and_validate_analysis, PYDANTIC_AVAILABLE
from .telemetry import PerfTracker, log_event, rotate_and_cleanup_logs, print_trace_summary, show_logs
from .db import init_db, save_record, toggle_star, seed_archetypes_if_needed, seed_starter_deck_if_needed, get_archetype
from .starter_deck import STARTER_DECK, ARCHETYPES

__all__ = [
    "DATA_DIR", "AUDIO_DIR", "DB_PATH", "LOG_PATH", "CONFIG_PATH", "WORKSPACE_DIR", "LOGS_DIR",
    "DEFAULT_CONFIG", "load_config", "save_config", "show_config_cli",
    "SENSITIVE_KEYWORDS", "detect_sensitive_content",
    "LinguoAnalysis", "parse_and_validate_analysis", "PYDANTIC_AVAILABLE",
    "PerfTracker", "log_event", "rotate_and_cleanup_logs", "print_trace_summary", "show_logs",
    "init_db", "save_record", "toggle_star", "seed_archetypes_if_needed", "seed_starter_deck_if_needed",
    "get_archetype", "STARTER_DECK", "ARCHETYPES"
]
