import subprocess
import tempfile
import os
from pathlib import Path

# Get the project root directory (parent of app directory)
PROJECT_ROOT = Path(__file__).parent.parent
WHISPER_PATH = str(PROJECT_ROOT / "whisper.cpp" / "build" / "bin" / "whisper-cli")
DEFAULT_MODEL = str(PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-base.en.bin")
MULTILINGUAL_MODEL = str(PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-base.bin")


def speech_to_text(audio_bytes: bytes, language: str = "en") -> str:
    """
    Convert speech to text using Whisper.
    
    Args:
        audio_bytes: Audio data in WAV format
        language: Language code (e.g., 'en', 'es'). Uses appropriate model.
    
    Returns:
        Transcribed text
    """
    from app.config.languages import get_language_config
    
    # Get language-specific model
    lang_config = get_language_config(language)
    model_path = lang_config.get('stt_model', DEFAULT_MODEL)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_file.write(audio_bytes)
        wav_path = temp_file.name

    # Whisper creates output as filename.wav.txt, not filename.txt
    txt_path = wav_path + ".txt"

    try:
        # Verify paths exist
        if not os.path.exists(WHISPER_PATH):
            raise FileNotFoundError(f"Whisper CLI not found at: {WHISPER_PATH}")
        if not os.path.exists(model_path):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Model not found at {model_path}, using default")
            model_path = DEFAULT_MODEL
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Whisper model not found at: {model_path}")
        
        # Check WAV file size
        wav_size = os.path.getsize(wav_path)
        if wav_size == 0:
            raise ValueError(f"Audio file is empty: {wav_path}")
        
        # Build command with language support
        cmd = [WHISPER_PATH, "-m", model_path, "-f", wav_path, "--no-timestamps", "-otxt"]
        
        # Add language parameter if not English (for multilingual model)
        if language != "en" and os.path.exists(MULTILINGUAL_MODEL):
            cmd.extend(["--language", language])
            # Use multilingual model for non-English
            if model_path == DEFAULT_MODEL:
                cmd[cmd.index("-m") + 1] = MULTILINGUAL_MODEL
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        
        # Log stderr for debugging
        if result.stderr:
            stderr_text = result.stderr.decode('utf-8', errors='ignore')
            if stderr_text.strip():
                print(f"Whisper stderr: {stderr_text}")
        
        # Check if output file was created
        if not os.path.exists(txt_path):
            error_msg = f"Whisper output file not created: {txt_path}"
            if result.stderr:
                error_msg += f"\nWhisper stderr: {result.stderr.decode('utf-8', errors='ignore')}"
            if result.stdout:
                error_msg += f"\nWhisper stdout: {result.stdout.decode('utf-8', errors='ignore')}"
            raise FileNotFoundError(error_msg)

        with open(txt_path, "r") as txt_file:
            text = txt_file.read().strip()
            return text if text else ""
    finally:
        # Clean up temp files
        if os.path.exists(wav_path):
            os.unlink(wav_path)
        if os.path.exists(txt_path):
            os.unlink(txt_path)