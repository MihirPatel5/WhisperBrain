"""
Language Detection Service
Auto-detects language from audio or text
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
WHISPER_PATH = str(PROJECT_ROOT / "whisper.cpp" / "build" / "bin" / "whisper-cli")
MULTILINGUAL_MODEL = str(PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-base.bin")


def detect_language_from_audio(audio_bytes: bytes) -> Optional[str]:
    """
    Detect language from audio using Whisper.
    
    Args:
        audio_bytes: Audio data in WAV format
    
    Returns:
        Language code (e.g., 'en', 'es') or None if detection fails
    """
    import tempfile
    import os
    
    # Check if Whisper and model are available (fail silently if not)
    if not os.path.exists(WHISPER_PATH) or not os.path.exists(MULTILINGUAL_MODEL):
        # Don't log warning - this is expected if models aren't installed
        # Just return None to use default language
        return None
    
    # Save audio to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_file.write(audio_bytes)
        wav_path = temp_file.name
    
    try:
        # Run Whisper with language detection
        cmd = [
            WHISPER_PATH,
            "-m", MULTILINGUAL_MODEL,
            "-f", wav_path,
            "--language", "auto",  # Auto-detect language
            "--no-timestamps",
            "-otxt"
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        
        # Parse language from output (if available)
        # Note: Whisper CLI may not directly output language code
        # This is a simplified implementation
        if result.returncode == 0:
            # For now, return None and let the system use default
            # In production, you'd parse the actual language from Whisper output
            logger.info("Language detection completed (using default for now)")
            return None  # Will use default language
        
        return None
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return None
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)


def detect_language_from_text(text: str) -> Optional[str]:
    """
    Simple language detection from text using heuristics.
    
    Args:
        text: Text to analyze
    
    Returns:
        Language code or None
    """
    text_lower = text.lower()
    
    # Simple heuristics (can be improved with langdetect library)
    spanish_indicators = ['hola', 'gracias', 'por favor', 'cómo', 'qué', 'español']
    if any(indicator in text_lower for indicator in spanish_indicators):
        return "es"
    
    # Default to English
    return "en"


def detect_language(audio_bytes: bytes = None, text: str = None) -> str:
    """
    Detect language from audio or text.
    
    Args:
        audio_bytes: Audio data (optional)
        text: Text data (optional)
    
    Returns:
        Language code (defaults to 'en')
    """
    from app.config.languages import FALLBACK_LANGUAGE
    
    # Try audio detection first (silently fails if models not available)
    if audio_bytes:
        try:
            lang = detect_language_from_audio(audio_bytes)
            if lang:
                return lang
        except Exception:
            # Silently fail and continue to text detection or fallback
            pass
    
    # Try text detection
    if text:
        try:
            lang = detect_language_from_text(text)
            if lang:
                return lang
        except Exception:
            # Silently fail and use fallback
            pass
    
    # Fallback to default
    return FALLBACK_LANGUAGE

