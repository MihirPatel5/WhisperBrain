"""
Audio Buffer Service
Manages in-memory audio buffering for real-time processing
"""
import io
import struct
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioBuffer:
    """
    In-memory audio buffer for real-time processing.
    Accumulates audio chunks and provides WAV format output.
    """
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        self.buffer = io.BytesIO()
        self.total_samples = 0
        self.wav_header_written = False
        
    def add_chunk(self, audio_data: bytes):
        """Add audio chunk to buffer"""
        if not self.wav_header_written:
            # Write WAV header
            self._write_wav_header()
            self.wav_header_written = True
        
        # Write audio data
        self.buffer.write(audio_data)
        # Estimate samples (rough calculation)
        self.total_samples += len(audio_data) // (self.channels * self.sample_width)
    
    def _write_wav_header(self):
        """Write WAV file header"""
        # We'll update the header later with correct size
        # For now, write placeholder header
        self.buffer.write(b'RIFF')
        self.buffer.write(struct.pack('<I', 0))  # File size (will update later)
        self.buffer.write(b'WAVE')
        self.buffer.write(b'fmt ')
        self.buffer.write(struct.pack('<I', 16))  # fmt chunk size
        self.buffer.write(struct.pack('<H', 1))   # Audio format (PCM)
        self.buffer.write(struct.pack('<H', self.channels))
        self.buffer.write(struct.pack('<I', self.sample_rate))
        self.buffer.write(struct.pack('<I', self.sample_rate * self.channels * self.sample_width))  # Byte rate
        self.buffer.write(struct.pack('<H', self.channels * self.sample_width))  # Block align
        self.buffer.write(struct.pack('<H', self.sample_width * 8))  # Bits per sample
        self.buffer.write(b'data')
        self.buffer.write(struct.pack('<I', 0))  # Data size (will update later)
    
    def _update_wav_header(self):
        """Update WAV header with correct file size"""
        data_size = self.buffer.tell() - 44  # Size of data chunk
        file_size = data_size + 36  # Total file size
        
        # Update file size
        self.buffer.seek(4)
        self.buffer.write(struct.pack('<I', file_size))
        
        # Update data size
        self.buffer.seek(40)
        self.buffer.write(struct.pack('<I', data_size))
        
        self.buffer.seek(0, io.SEEK_END)  # Return to end
    
    def get_wav_bytes(self) -> bytes:
        """Get complete WAV file as bytes"""
        if not self.wav_header_written:
            self._write_wav_header()
        
        # Update header with correct sizes
        current_pos = self.buffer.tell()
        self._update_wav_header()
        self.buffer.seek(current_pos)
        
        # Return all data
        self.buffer.seek(0)
        return self.buffer.read()
    
    def clear(self):
        """Clear buffer"""
        self.buffer = io.BytesIO()
        self.total_samples = 0
        self.wav_header_written = False
    
    def get_size(self) -> int:
        """Get current buffer size in bytes"""
        return self.buffer.tell()


class StreamingAudioProcessor:
    """
    Processes audio chunks in real-time without file I/O.
    Optimized for low latency.
    """
    
    def __init__(self):
        self.buffer = AudioBuffer()
        self.min_chunk_size = 16000  # Minimum bytes before processing (1 second at 16kHz)
        
    def add_chunk(self, audio_chunk: bytes) -> Optional[bytes]:
        """
        Add audio chunk and return WAV bytes if ready for processing.
        
        Args:
            audio_chunk: Raw audio data chunk
            
        Returns:
            WAV bytes if ready to process, None if still buffering
        """
        self.buffer.add_chunk(audio_chunk)
        
        # Return WAV bytes if we have enough data
        if self.buffer.get_size() >= self.min_chunk_size:
            wav_bytes = self.buffer.get_wav_bytes()
            self.buffer.clear()
            return wav_bytes
        
        return None
    
    def flush(self) -> Optional[bytes]:
        """Flush remaining buffer and return WAV bytes"""
        if self.buffer.get_size() > 44:  # More than just header
            wav_bytes = self.buffer.get_wav_bytes()
            self.buffer.clear()
            return wav_bytes
        return None

