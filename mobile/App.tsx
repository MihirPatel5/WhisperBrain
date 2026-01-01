import React, { useState, useRef, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  StatusBar,
  Alert,
  Platform,
} from 'react-native';
import { Audio } from 'expo-av';
// Using native WebSocket API

// Update this with your server IP and port
// For local development, use your computer's local IP (not localhost)
// Example: 'ws://192.168.1.100:8009/voice'
const WS_URL = 'ws://192.168.2.26:8009/voice'; // Replace with your server IP

export default function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState('Disconnected');
  const [error, setError] = useState<string | null>(null);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  
  const wsRef = useRef<any>(null);
  const soundRef = useRef<Audio.Sound | null>(null);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Request audio permissions
    (async () => {
      try {
        await Audio.requestPermissionsAsync();
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: true,
          playsInSilentModeIOS: true,
        });
      } catch (err) {
        console.error('Failed to get audio permissions', err);
        setError('Microphone permission denied');
      }
    })();

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
      if (recording) {
        recording.stopAndUnloadAsync();
      }
      if (soundRef.current) {
        soundRef.current.unloadAsync();
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        setIsConnected(true);
        setStatus('Connected');
        setError(null);
        console.log('WebSocket connected');
      };

      ws.onmessage = async (event: any) => {
        try {
          if (event.data instanceof Blob) {
            // Handle binary audio data
            console.log('Received audio response:', event.data.size, 'bytes');
            setIsProcessing(false);
            setStatus('Playing response...');
            
            const arrayBuffer = await event.data.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            // Convert to base64 manually to avoid spread operator issues
            let binary = '';
            for (let i = 0; i < uint8Array.length; i++) {
              binary += String.fromCharCode(uint8Array[i]);
            }
            const base64 = btoa(binary);
            const audioUri = `data:audio/wav;base64,${base64}`;
            await playSound(audioUri);
            
            setStatus(isConnected ? 'Connected' : 'Disconnected');
          } else if (typeof event.data === 'string') {
            // Handle JSON error messages or status updates
            try {
              const data = JSON.parse(event.data);
              if (data.error) {
                console.error('Backend error:', data.error);
                setError(data.error);
                setIsProcessing(false);
                setStatus(isConnected ? 'Connected' : 'Disconnected');
              } else if (data.status) {
                console.log('Backend status:', data.status);
                setStatus(data.status);
                if (data.text !== undefined) {
                  setTranscript(data.text);
                }
                if (data.response !== undefined) {
                  setResponse(data.response);
                  console.log('LLM response:', data.response);
                }
              }
            } catch (e) {
              // Not JSON, ignore
            }
          }
        } catch (err) {
          console.error('Error handling message:', err);
        }
      };

      ws.onerror = (error: any) => {
        console.error('WebSocket error:', error);
        setError('Connection error');
        setStatus('Error');
      };

      ws.onclose = () => {
        setIsConnected(false);
        setStatus('Disconnected');
        console.log('WebSocket disconnected');
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to connect:', err);
      setError('Failed to connect to server');
    }
  };

  const playSound = async (uri: string) => {
    try {
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
      }
      const { sound } = await Audio.Sound.createAsync({ uri });
      soundRef.current = sound;
      await sound.playAsync();
    } catch (err) {
      console.error('Error playing sound:', err);
    }
  };


  const startRecording = async () => {
    try {
      setError(null);

      if (!isConnected || !wsRef.current) {
        Alert.alert('Not Connected', 'Please connect to the server first');
        return;
      }

      const { recording: newRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );

      setRecording(newRecording);
      setIsRecording(true);
      setStatus('Recording...');
      setRecordingTime(0);
      
      // Start timer
      timerIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      console.log('Recording started');

    } catch (err) {
      console.error('Failed to start recording:', err);
      setError('Failed to start recording');
      setStatus('Error');
    }
  };

  const stopRecording = async () => {
    console.log('Stop recording called');
    
    // Stop timer
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    
    setIsRecording(false);
    
    if (recording) {
      try {
        await recording.stopAndUnloadAsync();
        const uri = recording.getURI();
        
        console.log('Recording stopped, URI:', uri);
        
        // Send complete audio file
        if (uri && wsRef.current?.readyState === WebSocket.OPEN) {
          setIsProcessing(true);
          setStatus('Processing...');
          
          try {
            const response = await fetch(uri);
            const blob = await response.blob();
            const arrayBuffer = await blob.arrayBuffer();
            
            console.log(`Sending audio: ${arrayBuffer.byteLength} bytes`);
            wsRef.current.send(arrayBuffer);
            console.log('Audio sent successfully');
          } catch (err) {
            console.error('Error sending audio:', err);
            setError('Failed to send audio');
            setIsProcessing(false);
            setStatus(isConnected ? 'Connected' : 'Disconnected');
          }
        } else {
          if (!uri) {
            setError('No audio recorded');
          } else if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            setError('WebSocket not connected');
          }
          setStatus(isConnected ? 'Connected' : 'Disconnected');
        }
        
        setRecording(null);
      } catch (err) {
        console.error('Error stopping recording:', err);
        setError('Failed to stop recording');
        setIsProcessing(false);
        setStatus(isConnected ? 'Connected' : 'Disconnected');
      }
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      
      <View style={styles.content}>
        <Text style={styles.title}>WhisperBrain</Text>
        <Text style={styles.subtitle}>Real-time conversation with AI</Text>

        <View style={styles.statusBar}>
          <View
            style={[
              styles.statusIndicator,
              isConnected ? styles.connected : styles.disconnected,
            ]}
          />
          <Text style={styles.statusText}>{status}</Text>
          {isRecording && (
            <Text style={styles.timer}>
              {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}
            </Text>
          )}
        </View>
        
        {isProcessing && (
          <View style={styles.processingIndicator}>
            <View style={styles.spinner} />
            <Text style={styles.processingText}>Processing your voice...</Text>
          </View>
        )}

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        <View style={styles.controls}>
          <TouchableOpacity
            style={[
              styles.recordButton,
              isRecording && styles.recordButtonActive,
              (!isConnected && !isRecording) && styles.recordButtonDisabled,
            ]}
            onPress={toggleRecording}
            disabled={!isConnected}
          >
            <Text style={styles.recordButtonText}>
              {isRecording ? '🛑 Stop' : '🎤 Record'}
            </Text>
          </TouchableOpacity>

          {!isConnected && (
            <TouchableOpacity
              style={styles.connectButton}
              onPress={connectWebSocket}
            >
              <Text style={styles.connectButtonText}>Connect</Text>
            </TouchableOpacity>
          )}
        </View>

        {transcript && (
          <View style={styles.transcriptContainer}>
            <Text style={styles.transcriptTitle}>Transcript:</Text>
            <Text style={styles.transcriptText}>{transcript}</Text>
          </View>
        )}
        
        {response && (
          <View style={styles.responseContainer}>
            <Text style={styles.responseTitle}>AI Response:</Text>
            <Text style={styles.responseText}>{response}</Text>
          </View>
        )}

        <View style={styles.infoContainer}>
          <Text style={styles.infoText}>
            {Platform.OS === 'ios'
              ? 'Press and hold to record'
              : 'Tap to start/stop recording'}
          </Text>
          <Text style={styles.infoText}>
            Make sure to update WS_URL in App.tsx with your server IP
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    backgroundColor: '#667eea',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 40,
    textAlign: 'center',
  },
  statusBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    marginBottom: 20,
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  connected: {
    backgroundColor: '#10b981',
  },
  disconnected: {
    backgroundColor: '#ef4444',
  },
  statusText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
  timer: {
    marginLeft: 'auto',
    fontWeight: '600',
    color: '#fff',
    fontFamily: 'monospace',
    fontSize: 16,
  },
  processingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 16,
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    borderWidth: 2,
    borderColor: '#3b82f6',
    borderRadius: 12,
    marginBottom: 20,
    width: '100%',
    maxWidth: 400,
  },
  spinner: {
    width: 20,
    height: 20,
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    borderTopColor: '#fff',
    borderRadius: 10,
  },
  processingText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  transcriptContainer: {
    marginTop: 20,
    padding: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    width: '100%',
    maxWidth: 400,
  },
  transcriptTitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 8,
    fontWeight: '600',
  },
  transcriptText: {
    color: '#fff',
    fontSize: 14,
    lineHeight: 20,
  },
  responseContainer: {
    marginTop: 16,
    padding: 16,
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.5)',
    borderRadius: 12,
    width: '100%',
    maxWidth: 400,
  },
  responseTitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 8,
    fontWeight: '600',
  },
  responseText: {
    color: '#fff',
    fontSize: 14,
    lineHeight: 20,
  },
  errorContainer: {
    backgroundColor: '#fee2e2',
    padding: 12,
    borderRadius: 8,
    marginBottom: 20,
    width: '100%',
    maxWidth: 400,
  },
  errorText: {
    color: '#dc2626',
    fontSize: 14,
    textAlign: 'center',
  },
  controls: {
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
    gap: 16,
  },
  recordButton: {
    backgroundColor: '#fff',
    paddingVertical: 20,
    paddingHorizontal: 40,
    borderRadius: 30,
    width: '100%',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  recordButtonActive: {
    backgroundColor: '#ef4444',
  },
  recordButtonDisabled: {
    opacity: 0.5,
  },
  recordButtonText: {
    color: '#667eea',
    fontSize: 20,
    fontWeight: '600',
  },
  connectButton: {
    backgroundColor: '#10b981',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 20,
  },
  connectButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  infoContainer: {
    marginTop: 40,
    padding: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    width: '100%',
    maxWidth: 400,
  },
  infoText: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 12,
    textAlign: 'center',
    marginBottom: 8,
  },
});

