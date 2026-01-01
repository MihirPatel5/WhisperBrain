import 'package:flutter/material.dart';

class ConversationWidget extends StatelessWidget {
  final List<Map<String, String>> conversationHistory;

  const ConversationWidget({
    super.key,
    required this.conversationHistory,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.95),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Conversation History',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 16),
          ...conversationHistory.map((msg) => _buildMessage(msg)),
        ],
      ),
    );
  }

  Widget _buildMessage(Map<String, String> msg) {
    final isUser = msg['role'] == 'user';
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            const Icon(Icons.smart_toy, color: Color(0xFF10b981), size: 20),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isUser
                    ? const Color(0xFFf0f4ff)
                    : const Color(0xFFf0fdf4),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: isUser
                      ? const Color(0xFF667eea)
                      : const Color(0xFF10b981),
                  width: 2,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isUser ? '👤 You' : '🤖 AI',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: isUser
                          ? const Color(0xFF667eea)
                          : const Color(0xFF10b981),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    msg['content'] ?? '',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.black87,
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 8),
            const Icon(Icons.person, color: Color(0xFF667eea), size: 20),
          ],
        ],
      ),
    );
  }
}

