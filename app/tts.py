import subprocess
import tempfile
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Get the project root directory (parent of app directory)
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_VOICE = str(PROJECT_ROOT / "voices" / "en_US-lessac-medium.onnx")


def text_to_speech(text: str, language: str = "en") -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        wav_path = temp_file.name

    try:
        from app.config.languages import get_language_config
        
        # Get language-specific voice model
        lang_config = get_language_config(language)
        voice_model = lang_config.get('tts_voice', DEFAULT_VOICE)
        
        if not os.path.exists(voice_model):
            logger.warning(f"Voice model not found at {voice_model}, using default")
            voice_model = DEFAULT_VOICE
            if not os.path.exists(voice_model):
                raise FileNotFoundError(f"Voice model not found at: {voice_model}")
        
        cmd = [
            "piper",
            "--model", voice_model,
            "--text", text,
            "--output-file", wav_path,
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"TTS output file not created: {wav_path}")

        with open(wav_path, "rb") as wav_file:
            return wav_file.read()
    finally:
        # Clean up temp file
        if os.path.exists(wav_path):
            os.unlink(wav_path)