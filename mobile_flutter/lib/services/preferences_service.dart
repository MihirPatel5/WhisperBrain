import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class PreferencesService {
  static const String _preferencesKey = 'whisperbrain_preferences';
  static Map<String, dynamic>? _cachedPreferences;

  /// Load preferences from local storage or API
  static Future<Map<String, dynamic>> loadPreferences() async {
    // Try local storage first
    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getString(_preferencesKey);
    
    if (stored != null) {
      try {
        _cachedPreferences = jsonDecode(stored) as Map<String, dynamic>;
        // Sync with server in background
        syncWithServer().catchError((e) => print('Sync error: $e'));
        return _cachedPreferences!;
      } catch (e) {
        print('Failed to parse stored preferences: $e');
      }
    }

    // Load from server
    try {
      final serverPrefs = await ApiService.getPreferences();
      if (serverPrefs != null) {
        _cachedPreferences = serverPrefs;
        await saveToLocalStorage();
        return serverPrefs;
      }
    } catch (e) {
      print('Failed to load preferences from server: $e');
    }

    // Return defaults
    _cachedPreferences = getDefaultPreferences();
    await saveToLocalStorage();
    return _cachedPreferences!;
  }

  /// Get current preferences
  static Future<Map<String, dynamic>> getPreferences() async {
    if (_cachedPreferences == null) {
      return await loadPreferences();
    }
    return _cachedPreferences!;
  }

  /// Update preferences
  static Future<Map<String, dynamic>> updatePreferences(
    Map<String, dynamic> updates,
  ) async {
    final current = await getPreferences();
    _cachedPreferences = {
      ...current,
      ...updates,
      'updated_at': DateTime.now().toIso8601String(),
    };

    // Save to local storage immediately
    await saveToLocalStorage();

    // Sync with server
    try {
      await ApiService.updatePreferences(updates);
    } catch (e) {
      print('Failed to sync preferences with server: $e');
    }

    return _cachedPreferences!;
  }

  /// Get a specific preference value
  static Future<T?> getPreference<T>(
    String category,
    String key,
    T? defaultValue,
  ) async {
    final prefs = await getPreferences();
    final categoryPrefs = prefs[category] as Map<String, dynamic>?;
    if (categoryPrefs == null) return defaultValue;
    return (categoryPrefs[key] as T?) ?? defaultValue;
  }

  /// Set a specific preference value
  static Future<void> setPreference(
    String category,
    String key,
    dynamic value,
  ) async {
    final current = await getPreferences();
    final categoryPrefs = Map<String, dynamic>.from(
      current[category] as Map<String, dynamic>? ?? {},
    );
    categoryPrefs[key] = value;

    await updatePreferences({category: categoryPrefs});
  }

  /// Reset to defaults
  static Future<Map<String, dynamic>> resetPreferences() async {
    try {
      final serverPrefs = await ApiService.resetPreferences();
      if (serverPrefs != null) {
        _cachedPreferences = serverPrefs;
        await saveToLocalStorage();
        return serverPrefs;
      }
    } catch (e) {
      print('Failed to reset preferences: $e');
    }

    _cachedPreferences = getDefaultPreferences();
    await saveToLocalStorage();
    return _cachedPreferences!;
  }

  /// Sync preferences with server
  static Future<void> syncWithServer() async {
    if (_cachedPreferences == null) return;

    try {
      await ApiService.updatePreferences(_cachedPreferences!);
    } catch (e) {
      print('Failed to sync preferences: $e');
    }
  }

  /// Save to local storage
  static Future<void> saveToLocalStorage() async {
    if (_cachedPreferences == null) return;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _preferencesKey,
      jsonEncode(_cachedPreferences),
    );
  }

  /// Get default preferences
  static Map<String, dynamic> getDefaultPreferences() {
    return {
      'audio': {
        'sample_rate': 16000,
        'quality': 'medium',
        'format': 'wav',
      },
      'ui': {
        'theme': 'light',
        'language': 'en',
        'animations': true,
      },
      'llm': {
        'default_model': 'phi3:mini',
        'temperature': 0.7,
        'max_tokens': 1000,
      },
      'features': {
        'vad_enabled': true,
        'emotion_detection': true,
        'translation': false,
        'rag_enabled': false,
        'tools_enabled': false,
      },
      'connection': {
        'auto_reconnect': true,
        'reconnect_delay': 3,
        'max_retries': 5,
      },
    };
  }
}

