/// Configuration for WebSocket connection
/// 
/// For local development:
///   - Use: ws://192.168.2.26:8009/voice
/// 
/// For Cloudflare Tunnel:
///   1. Install: npm install -g cloudflared
///   2. Run: cloudflared tunnel --url http://localhost:8009
///   3. Copy the HTTPS URL (e.g., https://xxxxx.trycloudflare.com)
///   4. Change ws:// to wss:// and add /voice
///   5. Example: wss://xxxxx.trycloudflare.com/voice
/// 
/// For ngrok:
///   1. Install: https://ngrok.com/download
///   2. Run: ngrok http 8009
///   3. Copy the HTTPS Forwarding URL (e.g., https://xxxxx.ngrok.io)
///   4. Change http:// to wss:// and add /voice
///   5. Example: wss://xxxxx.ngrok.io/voice

class AppConfig {
  // ============================================
  // CONFIGURATION - Update this URL
  // ============================================
  
  // Option 1: Local network (same WiFi)
  // static const String wsUrl = 'ws://192.168.2.26:8009/voice';
  
  // Option 2: Cloudflare Tunnel
  // Get URL from: cloudflared tunnel --url http://localhost:8009
  // Replace xxxxx with your actual tunnel URL
  // static const String wsUrl = 'wss://xxxxx.trycloudflare.com/voice';
  
  // Option 3: ngrok
  // Get URL from: ngrok http 8009
  // Replace xxxxx with your actual ngrok URL
  // static const String wsUrl = 'wss://xxxxx.ngrok.io/voice';
  
  // ============================================
  // Current active URL (uncomment one above)
  // ============================================
  static const String wsUrl = 'ws://192.168.2.26:8009/voice';
  
  // Helper to get URL from environment variable (optional)
  static String get wsUrlFromEnv {
    const envUrl = String.fromEnvironment('WS_URL');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }
    return wsUrl;
  }
}

