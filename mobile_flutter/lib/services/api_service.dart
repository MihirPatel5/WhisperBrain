import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

class ApiService {
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
  
  /// Get analytics statistics
  static Future<Map<String, dynamic>?> getAnalytics() async {
    try {
      final url = Uri.parse('$baseUrl/api/analytics');
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
  
  /// Get available models
  static Future<Map<String, dynamic>?> getModels() async {
    try {
      final url = Uri.parse('$baseUrl/api/models');
      final response = await http.get(url);
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Models error: $e');
      return null;
    }
  }
  
  /// Execute a tool
  static Future<Map<String, dynamic>?> executeTool(String toolName, Map<String, dynamic> parameters) async {
    try {
      final url = Uri.parse('$baseUrl/api/tools/execute');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'tool_name': toolName,
          'parameters': parameters,
        }),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Tool execution error: $e');
      return null;
    }
  }
  
  /// Add knowledge to RAG
  static Future<Map<String, dynamic>?> addKnowledge(String topic, String content, Map<String, dynamic>? metadata) async {
    try {
      final url = Uri.parse('$baseUrl/api/rag/knowledge');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'topic': topic,
          'content': content,
          'metadata': metadata ?? {},
        }),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Add knowledge error: $e');
      return null;
    }
  }
  
  /// Get RAG statistics
  static Future<Map<String, dynamic>?> getRagStats() async {
    try {
      final url = Uri.parse('$baseUrl/api/rag/stats');
      final response = await http.get(url);
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('RAG stats error: $e');
      return null;
    }
  }
  
  /// Get user preferences
  static Future<Map<String, dynamic>?> getPreferences() async {
    try {
      final url = Uri.parse('$baseUrl/api/preferences');
      final response = await http.get(url);
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Get preferences error: $e');
      return null;
    }
  }
  
  /// Update user preferences
  static Future<Map<String, dynamic>?> updatePreferences(Map<String, dynamic> preferences) async {
    try {
      final url = Uri.parse('$baseUrl/api/preferences');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(preferences),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Update preferences error: $e');
      return null;
    }
  }
  
  /// Reset preferences to defaults
  static Future<Map<String, dynamic>?> resetPreferences() async {
    try {
      final url = Uri.parse('$baseUrl/api/preferences/reset');
      final response = await http.post(url);
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Reset preferences error: $e');
      return null;
    }
  }
}

