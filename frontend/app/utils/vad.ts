/**
 * Voice Activity Detection (VAD) for frontend
 * Detects when user stops speaking to auto-stop recording
 */

export interface VADConfig {
  silenceThreshold?: number;      // Energy threshold for silence (0.0-1.0)
  minSilenceDuration?: number;     // Minimum silence duration in ms to trigger stop
  speechThreshold?: number;        // Energy threshold for speech detection
  sampleRate?: number;             // Audio sample rate
}

export class VoiceActivityDetector {
  private silenceThreshold: number;
  private minSilenceDuration: number;
  private speechThreshold: number;
  private sampleRate: number;
  
  private silenceStart: number | null = null;
  private isSpeaking: boolean = false;
  private lastSpeechTime: number = 0;

  constructor(config: VADConfig = {}) {
    this.silenceThreshold = config.silenceThreshold ?? 0.015;
    this.minSilenceDuration = config.minSilenceDuration ?? 1500; // 1.5 seconds
    this.speechThreshold = config.speechThreshold ?? 0.02;
    this.sampleRate = config.sampleRate ?? 16000;
  }

  /**
   * Reset VAD state (call when starting new recording)
   */
  reset(): void {
    this.silenceStart = null;
    this.isSpeaking = false;
    this.lastSpeechTime = 0;
  }

  /**
   * Calculate RMS energy of audio buffer
   */
  private calculateEnergy(audioBuffer: Float32Array): number {
    if (audioBuffer.length === 0) return 0;
    
    let sumSquares = 0;
    for (let i = 0; i < audioBuffer.length; i++) {
      sumSquares += audioBuffer[i] * audioBuffer[i];
    }
    
    const rms = Math.sqrt(sumSquares / audioBuffer.length);
    return rms;
  }

  /**
   * Process audio chunk and detect if speech has ended
   * @param audioBuffer - Audio data as Float32Array
   * @returns true if speech has ended and recording should stop
   */
  process(audioBuffer: Float32Array): boolean {
    const energy = this.calculateEnergy(audioBuffer);
    const now = Date.now();

    // Check if this chunk contains speech
    const hasSpeech = energy > this.speechThreshold;
    const isSilence = energy < this.silenceThreshold;

    if (hasSpeech) {
      // Speech detected
      this.isSpeaking = true;
      this.lastSpeechTime = now;
      this.silenceStart = null;
      return false; // Continue recording
    } else if (isSilence) {
      // Silence detected
      if (this.isSpeaking) {
        // We were speaking, now silence
        if (this.silenceStart === null) {
          this.silenceStart = now;
        } else {
          const silenceDuration = now - this.silenceStart;
          if (silenceDuration >= this.minSilenceDuration) {
            // Enough silence detected, speech has ended
            this.isSpeaking = false;
            return true; // Stop recording
          }
        }
      }
      return false; // Continue recording
    }

    return false; // Continue recording
  }

  /**
   * Check if currently speaking
   */
  getIsSpeaking(): boolean {
    return this.isSpeaking;
  }
}

