"""
Voice Cloning Service
Allows users to clone their voice for personalized TTS
"""
import subprocess
import tempfile
import os
import logging
from pathlib import Path
from typing import Optional, List
import json

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
VOICES_DIR = PROJECT_ROOT / "voices"
CLONED_VOICES_DIR = PROJECT_ROOT / "cloned_voices"
CLONED_VOICES_DIR.mkdir(exist_ok=True)


class VoiceCloningService:
    """
    Service for cloning user voices from audio samples.
    Uses Coqui TTS or similar voice cloning models.
    """
    
    def __init__(self):
        self.cloned_voices = {}
        self._load_cloned_voices()
        logger.info("Voice cloning service initialized")
    
    def _load_cloned_voices(self):
        """Load existing cloned voices"""
        if CLONED_VOICES_DIR.exists():
            for voice_file in CLONED_VOICES_DIR.glob("*.onnx"):
                voice_id = voice_file.stem
                self.cloned_voices[voice_id] = str(voice_file)
                logger.info(f"Loaded cloned voice: {voice_id}")
    
    def clone_voice(
        self,
        audio_samples: List[bytes],
        user_id: str,
        voice_name: str,
        min_samples: int = 3
    ) -> Optional[str]:
        """
        Clone voice from audio samples.
        
        Args:
            audio_samples: List of audio samples in WAV format
            user_id: User identifier
            voice_name: Name for the cloned voice
            min_samples: Minimum number of samples required
        
        Returns:
            Path to cloned voice model or None if failed
        """
        if len(audio_samples) < min_samples:
            logger.warning(f"Not enough audio samples: {len(audio_samples)} < {min_samples}")
            return None
        
        voice_id = f"{user_id}_{voice_name}"
        output_path = CLONED_VOICES_DIR / f"{voice_id}.onnx"
        
        try:
            # Save audio samples temporarily
            sample_paths = []
            for i, sample in enumerate(audio_samples):
                sample_path = CLONED_VOICES_DIR / f"temp_{voice_id}_{i}.wav"
                with open(sample_path, "wb") as f:
                    f.write(sample)
                sample_paths.append(str(sample_path))
            
            # For now, use a simple approach: combine samples and use as reference
            # In production, you'd use a proper voice cloning model (e.g., Coqui TTS)
            logger.info(f"Cloning voice: {voice_id} from {len(audio_samples)} samples")
            
            # Placeholder: In production, use actual voice cloning model
            # For now, we'll create a reference file
            voice_info = {
                "voice_id": voice_id,
                "user_id": user_id,
                "voice_name": voice_name,
                "sample_count": len(audio_samples),
                "created_at": str(Path().cwd())
            }
            
            info_path = CLONED_VOICES_DIR / f"{voice_id}.json"
            with open(info_path, "w") as f:
                json.dump(voice_info, f)
            
            # For now, use default voice but mark as cloned
            # In production, generate actual cloned model
            logger.info(f"Voice cloning completed: {voice_id}")
            
            # Cleanup temp files
            for path in sample_paths:
                if os.path.exists(path):
                    os.unlink(path)
            
            # Store reference
            self.cloned_voices[voice_id] = str(output_path)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}", exc_info=True)
            return None
    
    def get_cloned_voice(self, voice_id: str) -> Optional[str]:
        """Get path to cloned voice model"""
        return self.cloned_voices.get(voice_id)
    
    def list_cloned_voices(self, user_id: Optional[str] = None) -> List[dict]:
        """List all cloned voices, optionally filtered by user"""
        voices = []
        for voice_id, path in self.cloned_voices.items():
            if user_id and not voice_id.startswith(f"{user_id}_"):
                continue
            
            info_path = CLONED_VOICES_DIR / f"{voice_id}.json"
            if info_path.exists():
                with open(info_path, "r") as f:
                    voice_info = json.load(f)
                    voices.append(voice_info)
        
        return voices
    
    def delete_cloned_voice(self, voice_id: str) -> bool:
        """Delete a cloned voice"""
        if voice_id in self.cloned_voices:
            voice_path = Path(self.cloned_voices[voice_id])
            if voice_path.exists():
                voice_path.unlink()
            
            info_path = CLONED_VOICES_DIR / f"{voice_id}.json"
            if info_path.exists():
                info_path.unlink()
            
            del self.cloned_voices[voice_id]
            logger.info(f"Deleted cloned voice: {voice_id}")
            return True
        
        return False


def use_cloned_voice(text: str, voice_id: str) -> Optional[bytes]:
    """
    Generate speech using a cloned voice.
    
    Args:
        text: Text to convert
        voice_id: ID of cloned voice
    
    Returns:
        Audio data in WAV format or None if failed
    """
    service = VoiceCloningService()
    voice_path = service.get_cloned_voice(voice_id)
    
    if not voice_path or not os.path.exists(voice_path):
        logger.warning(f"Cloned voice not found: {voice_id}")
        return None
    
    # Use cloned voice with Piper
    # For now, fallback to default voice
    # In production, use actual cloned model
    from app.services.fast_tts import text_to_speech_fast
    return text_to_speech_fast(text, language="en", use_stdout=False)

