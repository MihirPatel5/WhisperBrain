import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:record/record.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:permission_handler/permission_handler.dart';
import '../services/audio_service.dart';
import '../services/websocket_service.dart';
import '../services/export_service.dart';
import '../widgets/conversation_widget.dart';
import '../widgets/recording_button.dart';
import '../widgets/status_indicator.dart';
import 'package:share_plus/share_plus.dart';
import 'package:cross_file/cross_file.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final WebSocketService _wsService = WebSocketService();
  final AudioService _audioService = AudioService();
  final AudioRecorder _recorder = AudioRecorder();
  final ExportService _exportService = ExportService();
  
  bool _isConnected = false;
  bool _isRecording = false;
  bool _isProcessing = false;
  String _status = 'Disconnected';
  String _currentTranscript = '';
  String _currentResponse = '';
  List<Map<String, String>> _conversationHistory = [];
  int _recordingSeconds = 0;
  Timer? _recordingTimer;
  String? _sessionId;
  String? _userId;
  bool _isReconnecting = false;
  int _reconnectAttempts = 0;
  Timer? _reconnectTimer;
  Map<String, dynamic>? _preferences;

  @override
  void initState() {
    super.initState();
    _requestPermissions();
  }

  @override
  void dispose() {
    _recordingTimer?.cancel();
    _recorder.dispose();
    _wsService.disconnect();
    _audioService.dispose();
    super.dispose();
  }

  Future<void> _requestPermissions() async {
    await [
      Permission.microphone,
      Permission.storage,
    ].request();
  }

  Future<void> _connectWebSocket() async {
    try {
      await _wsService.connect(
        onMessage: _handleWebSocketMessage,
        onError: _handleWebSocketError,
        onConnected: () {
          setState(() {
            _isConnected = true;
            _status = 'Connected';
          });
        },
        onDisconnected: () {
          setState(() {
            _isConnected = false;
            _status = 'Disconnected';
          });
        },
      );
    } catch (e) {
      setState(() {
        _status = 'Connection failed: $e';
      });
    }
  }

  void _handleWebSocketMessage(dynamic data) {
    if (data is String) {
      try {
        final json = jsonDecode(data);
        if (json['status'] != null) {
          setState(() {
            _status = json['status'];
            if (json['status'].toString().contains('Processing')) {
              _isProcessing = true;
            }
          });
        }
        if (json['text'] != null) {
          setState(() {
            _currentTranscript = json['text'];
          });
        }
        if (json['response'] != null) {
          setState(() {
            _currentResponse = json['response'];
            _isProcessing = false;
          });
          // Add to conversation history
          if (_currentTranscript.isNotEmpty && _currentResponse.isNotEmpty) {
            setState(() {
              _conversationHistory.add({
                'role': 'user',
                'content': _currentTranscript,
              });
              _conversationHistory.add({
                'role': 'assistant',
                'content': _currentResponse,
              });
              _currentTranscript = '';
              _currentResponse = '';
            });
          }
        }
        if (json['error'] != null) {
          setState(() {
            _status = 'Error: ${json['error']}';
            _isProcessing = false;
          });
        }
      } catch (e) {
        // Handle binary audio data
        _audioService.playAudio(data);
        setState(() {
          _isProcessing = false;
          _status = 'Playing response...';
        });
      }
    } else if (data is Uint8List) {
      // Binary audio data
      _audioService.playAudio(data);
      setState(() {
        _isProcessing = false;
        _status = 'Playing response...';
      });
    }
  }

  void _handleWebSocketError(dynamic error) {
    setState(() {
      _status = 'Error: $error';
      _isConnected = false;
      _isProcessing = false;
    });
  }

  Future<void> _startRecording() async {
    if (!_isConnected) {
      await _connectWebSocket();
      return;
    }

    try {
      if (await _recorder.hasPermission()) {
        final path = await AudioService.getTempPath();
        await _recorder.start(
          const RecordConfig(
            encoder: AudioEncoder.wav,
            sampleRate: 16000,
            numChannels: 1,
          ),
          path: path,
        );

        setState(() {
          _isRecording = true;
          _recordingSeconds = 0;
          _status = 'Recording...';
        });

        _recordingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
          setState(() {
            _recordingSeconds++;
          });
        });
      } else {
        setState(() {
          _status = 'Microphone permission denied';
        });
      }
    } catch (e) {
      setState(() {
        _status = 'Recording error: $e';
      });
    }
  }

  Future<void> _stopRecording() async {
    try {
      final path = await _recorder.stop();
      _recordingTimer?.cancel();

      setState(() {
        _isRecording = false;
        _status = 'Processing...';
        _isProcessing = true;
      });

      if (path != null) {
        final audioBytes = await AudioService.readAudioFile(path);
        _wsService.sendAudio(audioBytes);
      }
    } catch (e) {
      setState(() {
        _status = 'Stop recording error: $e';
        _isRecording = false;
      });
    }
  }

  void _clearConversation() {
    setState(() {
      _conversationHistory.clear();
      _currentTranscript = '';
      _currentResponse = '';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              const Color(0xFF667eea),
              const Color(0xFF764ba2),
              const Color(0xFFf093fb),
              const Color(0xFF4facfe),
            ],
            stops: const [0.0, 0.3, 0.6, 1.0],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                // Header
                Container(
                  padding: const EdgeInsets.all(24.0),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.95),
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 20,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      const Text(
                        'WhisperBrain',
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF667eea),
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Real-time conversation with AI',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey,
                        ),
                      ),
                      const SizedBox(height: 20),
                      // Status Indicator
                      StatusIndicator(
                        isConnected: _isConnected,
                        status: _status,
                        isProcessing: _isProcessing,
                      ),
                      const SizedBox(height: 20),
                      // Recording Timer
                      if (_isRecording)
                        Text(
                          'Recording: ${_formatTime(_recordingSeconds)}',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFFef4444),
                          ),
                        ),
                      const SizedBox(height: 20),
                      // Recording Button
                      RecordingButton(
                        isRecording: _isRecording,
                        isConnected: _isConnected,
                        onPressed: _isRecording ? _stopRecording : _startRecording,
                      ),
                      const SizedBox(height: 10),
                      // Connect Button
                      if (!_isConnected)
                        ElevatedButton(
                          onPressed: _connectWebSocket,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF10b981),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 32,
                              vertical: 16,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: const Text(
                            'Connect',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      // Clear Conversation Button
                      if (_conversationHistory.isNotEmpty)
                        TextButton(
                          onPressed: _clearConversation,
                          child: const Text(
                            'Clear Conversation',
                            style: TextStyle(
                              color: Color(0xFFef4444),
                              fontSize: 14,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                // Conversation History
                if (_conversationHistory.isNotEmpty)
                  ConversationWidget(conversationHistory: _conversationHistory),
                // Current Transcript
                if (_currentTranscript.isNotEmpty &&
                    !_conversationHistory.any((m) =>
                        m['role'] == 'user' && m['content'] == _currentTranscript))
                  _buildMessageCard(
                    'Current Input',
                    _currentTranscript,
                    Colors.blue,
                  ),
                // Current Response
                if (_currentResponse.isNotEmpty &&
                    !_conversationHistory.any((m) =>
                        m['role'] == 'assistant' && m['content'] == _currentResponse))
                  _buildMessageCard(
                    'AI Response',
                    _currentResponse,
                    Colors.green,
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMessageCard(String title, String content, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.95),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            content,
            style: const TextStyle(
              fontSize: 16,
              color: Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  String _formatTime(int seconds) {
    final minutes = seconds ~/ 60;
    final secs = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }
}

