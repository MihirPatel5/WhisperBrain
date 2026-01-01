"""
Fast TTS Service
Optimized text-to-speech with minimal file I/O
"""
import subprocess
import tempfile
import os
import logging
from pathlib import Path
import io

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_VOICE = str(PROJECT_ROOT / "voices" / "en_US-lessac-medium.onnx")


def text_to_speech_fast(text: str, language: str = "en", use_stdout: bool = True) -> bytes:
    """
    Fast text-to-speech with minimal file I/O.
    
    Args:
        text: Text to convert
        language: Language code
        use_stdout: Try to use stdout instead of temp file (faster)
    
    Returns:
        Audio data in WAV format
    """
    from app.config.languages import get_language_config
    
    # Get language-specific voice model
    lang_config = get_language_config(language)
    voice_model = lang_config.get('tts_voice', DEFAULT_VOICE)
    
    if not os.path.exists(voice_model):
        logger.warning(f"Voice model not found at {voice_model}, using default")
        voice_model = DEFAULT_VOICE
        if not os.path.exists(voice_model):
            raise FileNotFoundError(f"Voice model not found at: {voice_model}")
    
    # Try stdout first (faster, no file I/O)
    if use_stdout:
        try:
            return _process_via_stdout(text, voice_model)
        except Exception as e:
            logger.warning(f"Stdout processing failed: {e}, falling back to temp file")
    
    # Fallback to temp file
    return _process_via_temp_file(text, voice_model)


def _process_via_stdout(text: str, voice_model: str) -> bytes:
    """
    Process TTS via stdout (fastest method, no file I/O).
    Note: This requires Piper to support stdout output.
    """
    # Try to use stdout if supported
    cmd = [
        "piper",
        "--model", voice_model,
        "--text", text,
        "--output-file", "-"  # Try stdout
    ]
    
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False
    )
    
    if result.returncode == 0 and result.stdout:
        return result.stdout
    
    # If stdout not supported, fall back to temp file
    raise RuntimeError("Piper stdout not supported, using temp file")


def _process_via_temp_file(text: str, voice_model: str) -> bytes:
    """
    Process TTS via temp file (fallback method).
    Optimized to minimize I/O time.
    """
    # Use NamedTemporaryFile with delete=False for faster access
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        wav_path = temp_file.name
    
    try:
        cmd = [
            "piper",
            "--model", voice_model,
            "--text", text,
            "--output-file", wav_path,
        ]
        
        # Run with minimal overhead
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=True
        )
        
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"TTS output file not created: {wav_path}")
        
        # Read result quickly
        with open(wav_path, "rb") as wav_file:
            return wav_file.read()
    
    finally:
        # Fast cleanup
        try:
            if os.path.exists(wav_path):
                os.unlink(wav_path)
        except:
            pass  # Ignore cleanup errors

