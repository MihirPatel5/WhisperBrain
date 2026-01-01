"""
Language Configuration
Supports multiple languages for STT, TTS, and LLM
"""
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Supported languages configuration
SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "stt_model": str(PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-base.en.bin"),
        "tts_voice": str(PROJECT_ROOT / "voices" / "en_US-lessac-medium.onnx"),
        "code": "en",
    },
    "es": {
        "name": "Spanish",
        "stt_model": str(PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-base.bin"),  # Multilingual model
        "tts_voice": str(PROJECT_ROOT / "voices" / "en_US-lessac-medium.onnx"),  # Fallback to English if not available
        "code": "es",
    },
    # Add more languages as needed
    # "fr": {
    #     "name": "French",
    #     "stt_model": str(PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-base.bin"),
    #     "tts_voice": str(PROJECT_ROOT / "voices" / "fr_FR-medium.onnx"),
    #     "code": "fr",
    # },
}

# Default language
DEFAULT_LANGUAGE = "en"

# Language detection settings
AUTO_DETECT_LANGUAGE = True  # Auto-detect language from audio
FALLBACK_LANGUAGE = "en"     # Fallback if detection fails


def get_language_config(lang_code: str = None) -> dict:
    """
    Get language configuration.
    
    Args:
        lang_code: Language code (e.g., 'en', 'es'). Uses default if None.
    
    Returns:
        Language configuration dictionary
    """
    lang_code = lang_code or DEFAULT_LANGUAGE
    return SUPPORTED_LANGUAGES.get(lang_code, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE])


def is_language_supported(lang_code: str) -> bool:
    """Check if language is supported"""
    return lang_code in SUPPORTED_LANGUAGES


def get_available_languages() -> list:
    """Get list of available language codes"""
    return list(SUPPORTED_LANGUAGES.keys())

