import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import '../config.dart';

class Config {
  static String get baseUrl {
    // Extract base URL from WebSocket URL
    final wsUrl = 'ws://192.168.2.26:8009/voice'; // Update this to match your config
    if (wsUrl.startsWith('ws://')) {
      return wsUrl.replaceFirst('ws://', 'http://').replaceAll('/voice', '');
    } else if (wsUrl.startsWith('wss://')) {
      return wsUrl.replaceFirst('wss://', 'https://').replaceAll('/voice', '');
    }
    return 'http://192.168.2.26:8009';
  }
}

class ExportService {
  /// Export conversation to specified format
  Future<String?> exportConversation({
    required String sessionId,
    required List<Map<String, String>> conversationHistory,
    String format = 'json',
  }) async {
    try {
      final url = Uri.parse('${Config.baseUrl}/api/export');
      
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'session_id': sessionId,
          'conversation_history': conversationHistory,
          'format': format,
        }),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final content = data['content'] as String;
        final filename = data['filename'] as String;
        
        // Save to device
        final directory = await getApplicationDocumentsDirectory();
        final file = File('${directory.path}/$filename');
        await file.writeAsString(content);
        
        return file.path;
      }
      
      return null;
    } catch (e) {
      print('Export error: $e');
      return null;
    }
  }
  
  /// Get analytics
  Future<Map<String, dynamic>?> getAnalytics() async {
    try {
      final url = Uri.parse('${Config.baseUrl}/api/analytics');
      final response = await http.get(url);
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      
      return null;
    } catch (e) {
      print('Analytics error: $e');
      return null;
    }
  }
}

