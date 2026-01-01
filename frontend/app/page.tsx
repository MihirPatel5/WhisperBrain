'use client'

import { useState, useRef, useEffect } from 'react'
import styles from './page.module.css'
import { VoiceActivityDetector } from './utils/vad'
import { PreferencesService, UserPreferences } from './services/preferences'
import { ApiService } from './services/api'

export default function Home() {
  const [isRecording, setIsRecording] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [status, setStatus] = useState('Disconnected')
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [recordingTime, setRecordingTime] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  const [conversationHistory, setConversationHistory] = useState<Array<{role: string, content: string}>>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [userId, setUserId] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<any>(null) // Stores processor, stream, source
  const audioContextRef = useRef<AudioContext | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const audioChunksRef = useRef<Float32Array[]>([])
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const isRecordingRef = useRef<boolean>(false)
  const conversationEndRef = useRef<HTMLDivElement | null>(null)
  const vadRef = useRef<VoiceActivityDetector | null>(null)
  const [vadEnabled, setVadEnabled] = useState(true) // VAD enabled by default

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (mediaRecorderRef.current) {
        const recorder = mediaRecorderRef.current
        if (recorder.processor) {
          if (recorder.source) {
            recorder.source.disconnect()
          }
          if (recorder.gainNode) {
            recorder.gainNode.disconnect()
          }
          recorder.processor.disconnect()
        }
        if (recorder.stream) {
          recorder.stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
        }
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    // Clear previous conversation when reconnecting
    if (!isConnected) {
      setConversationHistory([])
      setTranscript('')
      setResponse('')
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Use environment variable or default to 8009
    const wsPort = process.env.NEXT_PUBLIC_WS_PORT || '8009'
    const wsUrl = `${protocol}//${window.location.hostname}:${wsPort}/voice`
    
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      setIsConnected(true)
      setStatus('Connected')
      setError(null)
      console.log('WebSocket connected')
    }
    
    ws.onmessage = async (event) => {
      // Handle session info from backend
      if (typeof event.data === 'string') {
        try {
          const data = JSON.parse(event.data)
          // Phase 3: Store session info
          if (data.session_id) {
            setSessionId(data.session_id)
          }
          if (data.user_id) {
            setUserId(data.user_id)
          }
        } catch (e) {
          // Not JSON, continue to original handler
        }
      }
      
      // Original message handler
      if (event.data instanceof Blob) {
        // Audio response
        console.log('Received audio response:', event.data.size, 'bytes')
        setIsProcessing(false)
        setStatus('Playing response...')
        
        const audioUrl = URL.createObjectURL(event.data)
        if (audioRef.current) {
          audioRef.current.src = audioUrl
          audioRef.current.onended = () => {
            setStatus(isConnected ? 'Connected' : 'Disconnected')
            URL.revokeObjectURL(audioUrl)
          }
          await audioRef.current.play().catch(console.error)
        }
      } else if (typeof event.data === 'string') {
        // JSON response (error or status)
        try {
          const data = JSON.parse(event.data)
          if (data.error) {
            console.error('Backend error:', data.error)
            setError(data.error)
            setIsProcessing(false)
            setStatus(isConnected ? 'Connected' : 'Disconnected')
          } else if (data.status) {
            console.log('Backend status:', data.status)
            setStatus(data.status)
            // Update transcript if provided
            if (data.text !== undefined) {
              setTranscript(data.text)
            }
            // Update response if provided
            if (data.response !== undefined) {
              setResponse(data.response)
              console.log('LLM response:', data.response)
              // Add to conversation history
              if (data.text && data.response) {
                setConversationHistory(prev => {
                  const newHistory = [
                    ...prev,
                    { role: 'user', content: data.text },
                    { role: 'assistant', content: data.response }
                  ]
                  // Scroll to bottom when new message added
                  setTimeout(() => {
                    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' })
                  }, 100)
                  return newHistory
                })
              }
            }
          }
        } catch (e) {
          // Not JSON, ignore
        }
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setError('Connection error')
      setStatus('Error')
    }
    
    ws.onclose = () => {
      setIsConnected(false)
      setStatus('Disconnected')
      console.log('WebSocket disconnected')
    }
    
    wsRef.current = ws
  }

  const startRecording = async () => {
    try {
      setError(null)
      
      // Connect WebSocket if not connected
      if (!isConnected || !wsRef.current) {
        connectWebSocket()
        // Wait a bit for connection
        await new Promise(resolve => setTimeout(resolve, 500))
      }

      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      })

      // Create audio context for processing
      audioContextRef.current = new AudioContext({ sampleRate: 16000 })
      const source = audioContextRef.current.createMediaStreamSource(stream)
      
      // Create ScriptProcessorNode to capture raw PCM audio
      const bufferSize = 4096
      const processor = audioContextRef.current.createScriptProcessor(bufferSize, 1, 1)
      
      // Clear previous chunks
      audioChunksRef.current = []
      
      // Initialize VAD if enabled
      if (vadEnabled) {
        vadRef.current = new VoiceActivityDetector({
          silenceThreshold: 0.015,
          minSilenceDuration: 1500, // 1.5 seconds of silence
          speechThreshold: 0.02,
          sampleRate: 16000
        })
        vadRef.current.reset()
        console.log('VAD enabled - will auto-stop on silence')
      }
      
      processor.onaudioprocess = (event) => {
        // Accumulate audio chunks while recording
        if (isRecordingRef.current) {
          const inputData = event.inputBuffer.getChannelData(0)
          audioChunksRef.current.push(new Float32Array(inputData))
          
          // VAD: Check if speech has ended
          if (vadEnabled && vadRef.current) {
            const speechEnded = vadRef.current.process(inputData)
            if (speechEnded) {
              console.log('VAD detected speech end, auto-stopping recording...')
              // Auto-stop recording
              setTimeout(() => {
                if (isRecordingRef.current) {
                  stopRecording()
                }
              }, 100) // Small delay to capture final chunk
              return
            }
          }
          
          // Log every 10 chunks to avoid spam
          if (audioChunksRef.current.length % 10 === 0) {
            console.log(`Captured ${audioChunksRef.current.length} audio chunks`)
          }
        }
      }
      
      // Connect the audio processing chain
      // ScriptProcessorNode needs to be connected to work, but we'll mute it
      const gainNode = audioContextRef.current.createGain()
      gainNode.gain.value = 0 // Mute to prevent feedback
      source.connect(processor)
      processor.connect(gainNode)
      gainNode.connect(audioContextRef.current.destination)
      
      // Store processor for cleanup
      ;(mediaRecorderRef.current as any) = { processor, stream, source, gainNode }
      isRecordingRef.current = true
      setIsRecording(true)
      setStatus('Recording...')
      setRecordingTime(0)
      
      // Start timer
      timerIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
      console.log('Recording started')
      // Clear current inputs when starting new recording
      setTranscript('')
      setResponse('')
      
      // Reset VAD if enabled
      if (vadEnabled && vadRef.current) {
        vadRef.current.reset()
      }
      
    } catch (err) {
      console.error('Error starting recording:', err)
      setError('Failed to start recording. Please check microphone permissions.')
      setStatus('Error')
    }
  }

  const stopRecording = async () => {
    console.log('Stop recording called')
    console.log(`Audio chunks accumulated: ${audioChunksRef.current.length}`)
    console.log(`WebSocket state: ${wsRef.current?.readyState}, OPEN=${WebSocket.OPEN}`)
    
    // Stop timer
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current)
      timerIntervalRef.current = null
    }
    
    isRecordingRef.current = false
    setIsRecording(false)
    
    // Wait a bit for any final audio chunks to be captured
    await new Promise(resolve => setTimeout(resolve, 200))
    
    if (mediaRecorderRef.current) {
      const recorder = mediaRecorderRef.current as any
      if (recorder.processor) {
        // Disconnect audio processing chain
        if (recorder.source) {
          recorder.source.disconnect()
        }
        if (recorder.gainNode) {
          recorder.gainNode.disconnect()
        }
        recorder.processor.disconnect()
        recorder.processor.onaudioprocess = null
      }
      if (recorder.stream) {
        recorder.stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
      }
      mediaRecorderRef.current = null
    }
    
    console.log(`Final audio chunks count: ${audioChunksRef.current.length}`)
    
    // Process and send accumulated audio
    if (audioChunksRef.current.length > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
      setIsProcessing(true)
      setStatus('Processing...')
      
      try {
        console.log(`Processing ${audioChunksRef.current.length} audio chunks`)
        
        // Create AudioBuffer from all accumulated chunks
        const totalLength = audioChunksRef.current.reduce((sum, chunk) => sum + chunk.length, 0)
        const audioBuffer = audioContextRef.current!.createBuffer(
          1,
          totalLength,
          audioContextRef.current!.sampleRate
        )
        const channelData = audioBuffer.getChannelData(0)
        let offset = 0
        for (const chunk of audioChunksRef.current) {
          channelData.set(chunk, offset)
          offset += chunk.length
        }
        
        // Convert to WAV
        const wavBuffer = audioBufferToWav(audioBuffer)
        console.log(`Sending audio: ${wavBuffer.byteLength} bytes`)
        
        // Send to backend
        wsRef.current.send(wavBuffer)
        
        // Clear chunks
        audioChunksRef.current = []
        
        console.log('Audio sent successfully')
      } catch (err) {
        console.error('Error processing audio:', err)
        setError('Failed to process audio')
        setIsProcessing(false)
        setStatus(isConnected ? 'Connected' : 'Disconnected')
      }
      } else {
        console.warn('No audio chunks to send or WebSocket not open')
        if (audioChunksRef.current.length === 0) {
          setError('No audio captured. Please try recording again.')
        } else if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          setError('WebSocket not connected. Please reconnect.')
        }
        setStatus(isConnected ? 'Connected' : 'Disconnected')
      }
    }

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  const handleExportConversation = async (format: 'json' | 'text' | 'markdown') => {
    if (!sessionId || conversationHistory.length === 0) {
      setError('No conversation to export')
      return
    }

    try {
      setStatus('Exporting conversation...')
      const result = await ApiService.exportConversation(sessionId, conversationHistory, format)
      
      // Handle response - backend returns { content, filename, ... }
      const content = result.content || JSON.stringify(result, null, 2)
      const filename = result.filename || `conversation_${Date.now()}.${format === 'json' ? 'json' : format === 'markdown' ? 'md' : 'txt'}`
      
      // Create download link
      const blob = new Blob([content], {
        type: format === 'json' ? 'application/json' : format === 'markdown' ? 'text/markdown' : 'text/plain'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      setStatus('Export completed')
      setTimeout(() => {
        setStatus(isConnected ? 'Connected' : 'Disconnected')
      }, 2000)
    } catch (err: any) {
      console.error('Export error:', err)
      setError(`Export failed: ${err.message || 'Unknown error'}`)
      setStatus(isConnected ? 'Connected' : 'Disconnected')
    }
  }

  // Convert AudioBuffer to WAV format
  const audioBufferToWav = (buffer: AudioBuffer): ArrayBuffer => {
    const length = buffer.length
    const numberOfChannels = buffer.numberOfChannels
    const sampleRate = buffer.sampleRate
    const arrayBuffer = new ArrayBuffer(44 + length * numberOfChannels * 2)
    const view = new DataView(arrayBuffer)
    const channels: Float32Array[] = []
    let offset = 0
    let pos = 0

    // Write WAV header
    const setUint16 = (data: number) => {
      view.setUint16(pos, data, true)
      pos += 2
    }
    const setUint32 = (data: number) => {
      view.setUint32(pos, data, true)
      pos += 4
    }

    // RIFF identifier
    setUint32(0x46464952) // "RIFF"
    setUint32(36 + length * numberOfChannels * 2) // file length - 8
    setUint32(0x45564157) // "WAVE"
    setUint32(0x20746d66) // "fmt " chunk
    setUint32(16) // format chunk length
    setUint16(1) // sample format (raw)
    setUint16(numberOfChannels)
    setUint32(sampleRate)
    setUint32(sampleRate * numberOfChannels * 2) // byte rate
    setUint16(numberOfChannels * 2) // block align
    setUint16(16) // bits per sample
    setUint32(0x61746164) // "data" chunk
    setUint32(length * numberOfChannels * 2)

    // Write interleaved data
    for (let i = 0; i < numberOfChannels; i++) {
      channels.push(buffer.getChannelData(i))
    }

    while (offset < length) {
      for (let i = 0; i < numberOfChannels; i++) {
        let sample = Math.max(-1, Math.min(1, channels[i][offset]))
        sample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
        view.setInt16(pos, sample, true)
        pos += 2
      }
      offset++
    }

    return arrayBuffer
  }

  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <h1 className={styles.title}>WhisperBrain</h1>
        <p className={styles.subtitle}>Real-time conversation with AI</p>

        <div className={styles.statusBar}>
          <div className={`${styles.statusIndicator} ${isConnected ? styles.connected : styles.disconnected}`} />
          <span className={styles.statusText}>{status}</span>
          {isRecording && (
            <span className={styles.timer}>
              {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}
            </span>
          )}
        </div>
        
        {isProcessing && (
          <div className={styles.processingIndicator}>
            <div className={styles.spinner}></div>
            <span>Processing your voice...</span>
          </div>
        )}

        {error && (
          <div className={styles.error}>
            {error}
          </div>
        )}

        <div className={styles.controls}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', alignItems: 'center', width: '100%' }}>
            <button
              className={`${styles.recordButton} ${isRecording ? styles.recording : ''}`}
              onClick={toggleRecording}
              disabled={!isConnected && !isRecording}
            >
              <div className={styles.micIcon}>
                {isRecording ? '🎤' : '🎙️'}
              </div>
              <span>{isRecording ? 'Stop Recording' : 'Start Recording'}</span>
            </button>
            
            {/* VAD Toggle */}
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.5rem', 
              fontSize: '0.9rem', 
              color: '#666', 
              cursor: isRecording ? 'not-allowed' : 'pointer',
              opacity: isRecording ? 0.6 : 1
            }}>
              <input
                type="checkbox"
                checked={vadEnabled}
                onChange={(e) => {
                  setVadEnabled(e.target.checked)
                  if (!e.target.checked && vadRef.current) {
                    vadRef.current.reset()
                  }
                }}
                disabled={isRecording}
                style={{ cursor: isRecording ? 'not-allowed' : 'pointer' }}
              />
              <span>Auto-stop on silence (VAD)</span>
            </label>
          </div>

          {!isConnected && (
            <button
              className={styles.connectButton}
              onClick={connectWebSocket}
            >
              Connect
            </button>
          )}

          {conversationHistory.length > 0 && (
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
              <button
                className={styles.clearButton}
                onClick={() => {
                  setConversationHistory([])
                  setTranscript('')
                  setResponse('')
                }}
              >
                Clear Conversation
              </button>
              <button
                className={styles.exportButton}
                onClick={() => handleExportConversation('json')}
                title="Export as JSON"
              >
                📥 Export JSON
              </button>
              <button
                className={styles.exportButton}
                onClick={() => handleExportConversation('text')}
                title="Export as Text"
              >
                📄 Export Text
              </button>
            </div>
          )}
        </div>

        {/* Conversation History */}
        {conversationHistory.length > 0 && (
          <div className={styles.conversationContainer}>
            <h3 className={styles.conversationTitle}>Conversation History</h3>
            <div className={styles.conversationList}>
              {conversationHistory.map((msg, idx) => (
                <div key={idx} className={msg.role === 'user' ? styles.userMessage : styles.assistantMessage}>
                  <div className={styles.messageHeader}>
                    <span className={styles.messageRole}>{msg.role === 'user' ? '👤 You' : '🤖 AI'}</span>
                  </div>
                  <div className={styles.messageContent}>{msg.content}</div>
                </div>
              ))}
              <div ref={conversationEndRef} />
            </div>
          </div>
        )}

        {/* Current Transcript (if not yet in history) */}
        {transcript && !conversationHistory.some(m => m.role === 'user' && m.content === transcript) && (
          <div className={styles.transcript}>
            <h3>Current Input:</h3>
            <p>{transcript}</p>
          </div>
        )}
        
        {/* Current Response (if not yet in history) */}
        {response && !conversationHistory.some(m => m.role === 'assistant' && m.content === response) && (
          <div className={styles.response}>
            <h3>AI Response:</h3>
            <p>{response}</p>
          </div>
        )}

        <audio ref={audioRef} className={styles.audioPlayer} />
      </div>
    </main>
  )
}

