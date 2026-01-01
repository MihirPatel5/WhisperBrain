"""
Fast STT Service
Optimized speech-to-text with minimal file I/O
"""
import subprocess
import tempfile
import os
import logging
from pathlib import Path
from typing import Optional
import io

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
WHISPER_PATH = str(PROJECT_ROOT / "whisper.cpp" / "build" / "bin" / "whisper-cli")
DEFAULT_MODEL = str(PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-base.en.bin")
MULTILINGUAL_MODEL = str(PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-base.bin")


def speech_to_text_fast(audio_bytes: bytes, language: str = "en", use_stdin: bool = True) -> str:
    """
    Fast speech-to-text with minimal file I/O.
    
    Args:
        audio_bytes: Audio data in WAV format (in memory)
        language: Language code
        use_stdin: Try to use stdin instead of temp file (faster)
    
    Returns:
        Transcribed text
    """
    from app.config.languages import get_language_config
    
    # Get language-specific model
    lang_config = get_language_config(language)
    model_path = lang_config.get('stt_model', DEFAULT_MODEL)
    
    if not os.path.exists(WHISPER_PATH):
        raise FileNotFoundError(f"Whisper CLI not found at: {WHISPER_PATH}")
    if not os.path.exists(model_path):
        logger.warning(f"Model not found at {model_path}, using default")
        model_path = DEFAULT_MODEL
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Whisper model not found at: {model_path}")
    
    # Try stdin first (faster, no file I/O)
    if use_stdin:
        try:
            return _process_via_stdin(audio_bytes, model_path, language)
        except Exception as e:
            logger.warning(f"Stdin processing failed: {e}, falling back to temp file")
    
    # Fallback to temp file (if stdin not supported)
    return _process_via_temp_file(audio_bytes, model_path, language)


def _process_via_stdin(audio_bytes: bytes, model_path: str, language: str) -> str:
    """
    Process audio via stdin (fastest method, no file I/O).
    Note: This requires Whisper to support stdin input.
    """
    # Build command
    cmd = [WHISPER_PATH, "-m", model_path, "-f", "-", "--no-timestamps", "-otxt"]
    
    # Add language parameter if not English
    if language != "en" and os.path.exists(MULTILINGUAL_MODEL):
        cmd.extend(["--language", language])
        if model_path == DEFAULT_MODEL:
            cmd[cmd.index("-m") + 1] = MULTILINGUAL_MODEL
    
    # Run with stdin input
    result = subprocess.run(
        cmd,
        input=audio_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False
    )
    
    if result.returncode != 0:
        error_msg = result.stderr.decode('utf-8', errors='ignore')
        raise RuntimeError(f"Whisper failed: {error_msg}")
    
    # Parse output from stdout
    output = result.stdout.decode('utf-8', errors='ignore').strip()
    
    # If Whisper outputs to file, we need to read it
    # For now, try to extract text from stdout
    if output:
        return output
    
    # If no stdout, Whisper might have written to file
    # This is a limitation - we'll use temp file method
    raise RuntimeError("Whisper stdin method not fully supported, using temp file")


def _process_via_temp_file(audio_bytes: bytes, model_path: str, language: str) -> str:
    """
    Process audio via temp file (fallback method).
    Optimized to minimize I/O time.
    """
    # Use NamedTemporaryFile with delete=False for faster access
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_file.write(audio_bytes)
        wav_path = temp_file.name
    
    txt_path = wav_path + ".txt"
    
    try:
        # Build command
        cmd = [WHISPER_PATH, "-m", model_path, "-f", wav_path, "--no-timestamps", "-otxt"]
        
        if language != "en" and os.path.exists(MULTILINGUAL_MODEL):
            cmd.extend(["--language", language])
            if model_path == DEFAULT_MODEL:
                cmd[cmd.index("-m") + 1] = MULTILINGUAL_MODEL
        
        # Run with minimal overhead
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False
        )
        
        # Check if output file was created
        if not os.path.exists(txt_path):
            error_msg = f"Whisper output file not created: {txt_path}"
            if result.stderr:
                error_msg += f"\nStderr: {result.stderr.decode('utf-8', errors='ignore')}"
            raise FileNotFoundError(error_msg)
        
        # Read result quickly
        with open(txt_path, "r") as txt_file:
            text = txt_file.read().strip()
            return text if text else ""
    
    finally:
        # Fast cleanup
        try:
            if os.path.exists(wav_path):
                os.unlink(wav_path)
            if os.path.exists(txt_path):
                os.unlink(txt_path)
        except:
            pass  # Ignore cleanup errors


def speech_to_text_streaming(audio_chunks: list, language: str = "en") -> str:
    """
    Process streaming audio chunks for real-time transcription.
    Accumulates chunks and processes when ready.
    
    Args:
        audio_chunks: List of audio chunks (bytes)
        language: Language code
    
    Returns:
        Transcribed text
    """
    # Combine chunks in memory
    combined = b''.join(audio_chunks)
    
    # Process combined audio
    return speech_to_text_fast(combined, language)

