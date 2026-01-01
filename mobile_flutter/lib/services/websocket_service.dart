import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../config.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  Function(dynamic)? _onMessage;
  Function(dynamic)? _onError;
  VoidCallback? _onConnected;
  VoidCallback? _onDisconnected;

  // Get URL from config (can be updated for Cloudflare Tunnel or ngrok)
  static String get _baseUrl => AppConfig.wsUrlFromEnv;

  Future<void> connect({
    required Function(dynamic) onMessage,
    required Function(dynamic) onError,
    required VoidCallback onConnected,
    required VoidCallback onDisconnected,
  }) async {
    _onMessage = onMessage;
    _onError = onError;
    _onConnected = onConnected;
    _onDisconnected = onDisconnected;

    try {
      _channel = WebSocketChannel.connect(Uri.parse(_baseUrl));
      
      _channel!.stream.listen(
        (data) {
          if (data is String) {
            try {
              final json = jsonDecode(data);
              _onMessage?.call(json);
            } catch (e) {
              // If not JSON, might be base64 encoded audio
              _onMessage?.call(data);
            }
          } else if (data is List<int>) {
            // Binary audio data
            _onMessage?.call(Uint8List.fromList(data));
          } else if (data is Uint8List) {
            // Already Uint8List
            _onMessage?.call(data);
          } else {
            _onMessage?.call(data);
          }
        },
        onError: (error) {
          _onError?.call(error);
        },
        onDone: () {
          _onDisconnected?.call();
        },
        cancelOnError: false,
      );

      _onConnected?.call();
    } catch (e) {
      _onError?.call(e);
      rethrow;
    }
  }

  void sendAudio(Uint8List audioBytes) {
    if (_channel != null) {
      try {
        _channel!.sink.add(audioBytes);
      } catch (e) {
        _onError?.call(e);
      }
    }
  }

  void disconnect() {
    _channel?.sink.close();
    _channel = null;
  }

  bool get isConnected => _channel != null;
}

