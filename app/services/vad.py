"""
Voice Activity Detection (VAD) Service
Detects when user stops speaking to auto-stop recording
"""
import time
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """
    Detects voice activity in audio streams.
    Automatically detects when speech ends based on silence detection.
    """
    
    def __init__(
        self,
        silence_threshold: float = 0.01,
        min_silence_duration: float = 1.5,
        speech_threshold: float = 0.02,
        sample_rate: int = 16000
    ):
        """
        Initialize VAD with configurable parameters.
        
        Args:
            silence_threshold: RMS energy below this is considered silence (0.0-1.0)
            min_silence_duration: Minimum seconds of silence to trigger speech end
            speech_threshold: RMS energy above this is considered speech
            sample_rate: Audio sample rate (Hz)
        """
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        self.speech_threshold = speech_threshold
        self.sample_rate = sample_rate
        
        # State tracking
        self.silence_start: Optional[float] = None
        self.last_speech_time: Optional[float] = None
        self.is_speaking = False
        self.silence_samples = 0
        self.speech_samples = 0
        
        logger.info(f"VAD initialized: silence_threshold={silence_threshold}, "
                   f"min_silence_duration={min_silence_duration}s")
    
    def reset(self):
        """Reset VAD state (call when starting new recording)"""
        self.silence_start = None
        self.last_speech_time = None
        self.is_speaking = False
        self.silence_samples = 0
        self.speech_samples = 0
        logger.debug("VAD state reset")
    
    def calculate_rms_energy(self, audio_data: bytes) -> float:
        """
        Calculate RMS (Root Mean Square) energy of audio chunk.
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            
        Returns:
            Normalized RMS energy (0.0-1.0)
        """
        try:
            # Convert bytes to numpy array (16-bit signed integers)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return 0.0
            
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            
            # Normalize to 0.0-1.0 range (16-bit audio max is 32768)
            normalized_rms = min(rms / 32768.0, 1.0)
            
            return normalized_rms
        except Exception as e:
            logger.warning(f"Error calculating RMS: {e}")
            return 0.0
    
    def process_chunk(self, audio_chunk: bytes) -> dict:
        """
        Process an audio chunk and detect speech activity.
        
        Args:
            audio_chunk: Raw audio bytes
            
        Returns:
            dict with 'is_speaking', 'speech_ended', 'energy' keys
        """
        current_time = time.time()
        energy = self.calculate_rms_energy(audio_chunk)
        
        # Determine if this chunk contains speech
        has_speech = energy > self.speech_threshold
        is_silence = energy < self.silence_threshold
        
        # Update state
        if has_speech:
            self.is_speaking = True
            self.last_speech_time = current_time
            self.silence_start = None
            self.speech_samples += 1
            self.silence_samples = 0
        elif is_silence:
            self.silence_samples += 1
            
            # Start tracking silence period
            if self.silence_start is None and self.is_speaking:
                self.silence_start = current_time
                logger.debug(f"Silence started after speech (energy: {energy:.4f})")
        
        # Check if speech has ended
        speech_ended = False
        if self.is_speaking and self.silence_start is not None:
            silence_duration = current_time - self.silence_start
            if silence_duration >= self.min_silence_duration:
                speech_ended = True
                self.is_speaking = False
                logger.info(f"Speech ended: {silence_duration:.2f}s of silence detected")
        
        return {
            'is_speaking': self.is_speaking,
            'speech_ended': speech_ended,
            'energy': energy,
            'silence_duration': (current_time - self.silence_start) if self.silence_start else 0.0
        }
    
    def should_stop_recording(self, audio_chunk: bytes) -> bool:
        """
        Check if recording should stop based on silence detection.
        
        Args:
            audio_chunk: Raw audio bytes
            
        Returns:
            True if speech has ended and recording should stop
        """
        result = self.process_chunk(audio_chunk)
        return result['speech_ended']


class SimpleVAD:
    """
    Simplified VAD for quick implementation.
    Uses basic energy-based detection.
    """
    
    def __init__(self, silence_threshold: float = 0.015, min_silence_ms: int = 1500):
        self.silence_threshold = silence_threshold
        self.min_silence_ms = min_silence_ms
        self.silence_start = None
        self.is_speaking = False
    
    def reset(self):
        self.silence_start = None
        self.is_speaking = False
    
    def check(self, audio_chunk: bytes) -> bool:
        """
        Check if speech has ended.
        Returns True if should stop recording.
        """
        import time
        
        # Simple energy calculation
        try:
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            if len(audio_array) == 0:
                return False
            
            energy = np.abs(audio_array).mean() / 32768.0
            
            if energy > self.silence_threshold:
                # Speech detected
                self.is_speaking = True
                self.silence_start = None
                return False
            else:
                # Silence detected
                if self.is_speaking:
                    # We were speaking, now silence
                    if self.silence_start is None:
                        self.silence_start = time.time() * 1000  # milliseconds
                    else:
                        silence_duration = (time.time() * 1000) - self.silence_start
                        if silence_duration >= self.min_silence_ms:
                            # Enough silence, speech ended
                            self.is_speaking = False
                            return True
                return False
        except Exception as e:
            logger.warning(f"VAD check error: {e}")
            return False

