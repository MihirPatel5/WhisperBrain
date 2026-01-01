"""
Voice Cloning API Endpoints
Handles voice upload and cloning requests
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/clone")
async def clone_voice(
    user_id: str,
    voice_name: str,
    audio_samples: List[UploadFile] = File(...)
):
    """
    Clone user voice from audio samples.
    
    Args:
        user_id: User identifier
        voice_name: Name for the cloned voice
        audio_samples: List of audio files (WAV format)
    
    Returns:
        Voice ID and status
    """
    from app.services.voice_cloning import VoiceCloningService
    
    try:
        service = VoiceCloningService()
        
        # Read audio samples
        audio_data = []
        for sample in audio_samples:
            data = await sample.read()
            audio_data.append(data)
        
        # Clone voice
        voice_path = service.clone_voice(
            audio_samples=audio_data,
            user_id=user_id,
            voice_name=voice_name
        )
        
        if voice_path:
            return {
                "status": "success",
                "voice_id": f"{user_id}_{voice_name}",
                "voice_path": voice_path
            }
        else:
            raise HTTPException(status_code=400, detail="Voice cloning failed")
    
    except Exception as e:
        logger.error(f"Voice cloning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_cloned_voices(user_id: str = None):
    """
    List cloned voices.
    
    Args:
        user_id: Optional user ID to filter
    
    Returns:
        List of cloned voices
    """
    from app.services.voice_cloning import VoiceCloningService
    
    try:
        service = VoiceCloningService()
        voices = service.list_cloned_voices(user_id=user_id)
        return {"status": "success", "voices": voices}
    
    except Exception as e:
        logger.error(f"List voices error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{voice_id}")
async def delete_cloned_voice(voice_id: str):
    """
    Delete a cloned voice.
    
    Args:
        voice_id: Voice ID to delete
    
    Returns:
        Deletion status
    """
    from app.services.voice_cloning import VoiceCloningService
    
    try:
        service = VoiceCloningService()
        success = service.delete_cloned_voice(voice_id)
        
        if success:
            return {"status": "success", "message": f"Voice {voice_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Voice not found")
    
    except Exception as e:
        logger.error(f"Delete voice error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

