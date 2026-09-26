"""
Linguo Audio Module
Speech synthesis (Kokoro-82M, Edge-TTS, macOS say) and audio caching.
"""

from .engine import synthesize_english, synthesize_thai, preload_thai_audio_cache, FFMPEG_BIN

__all__ = ["synthesize_english", "synthesize_thai", "preload_thai_audio_cache", "FFMPEG_BIN"]
