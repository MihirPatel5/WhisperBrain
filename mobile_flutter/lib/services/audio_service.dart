import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:audioplayers/audioplayers.dart';
import 'package:path_provider/path_provider.dart';

class AudioService {
  final AudioPlayer _player = AudioPlayer();

  static Future<String> getTempPath() async {
    final directory = await getTemporaryDirectory();
    return '${directory.path}/recording_${DateTime.now().millisecondsSinceEpoch}.wav';
  }

  static Future<Uint8List> readAudioFile(String path) async {
    final file = File(path);
    return await file.readAsBytes();
  }

  Future<void> playAudio(dynamic audioData) async {
    try {
      if (audioData is Uint8List) {
        // Save to temp file and play
        final tempDir = await getTemporaryDirectory();
        final tempPath = '${tempDir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.wav';
        final file = File(tempPath);
        await file.writeAsBytes(audioData);
        
        await _player.play(DeviceFileSource(tempPath));
        
        // Clean up after playback
        _player.onPlayerComplete.listen((_) {
          file.delete();
        });
      } else if (audioData is String) {
        // Try to decode base64 if needed
        try {
          final bytes = base64Decode(audioData);
          await playAudio(bytes);
        } catch (e) {
          // If not base64, treat as file path
          await _player.play(DeviceFileSource(audioData));
        }
      }
    } catch (e) {
      print('Error playing audio: $e');
    }
  }

  void dispose() {
    _player.dispose();
  }
}

