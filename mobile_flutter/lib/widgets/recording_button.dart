import 'package:flutter/material.dart';

class RecordingButton extends StatelessWidget {
  final bool isRecording;
  final bool isConnected;
  final VoidCallback onPressed;

  const RecordingButton({
    super.key,
    required this.isRecording,
    required this.isConnected,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: isConnected ? onPressed : null,
      child: Container(
        width: 120,
        height: 120,
        decoration: BoxDecoration(
          gradient: isRecording
              ? const LinearGradient(
                  colors: [Color(0xFFef4444), Color(0xFFdc2626)],
                )
              : const LinearGradient(
                  colors: [Color(0xFF667eea), Color(0xFF764ba2)],
                ),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: (isRecording ? Colors.red : Colors.purple).withOpacity(0.4),
              blurRadius: 20,
              spreadRadius: 5,
            ),
          ],
        ),
        child: Center(
          child: Icon(
            isRecording ? Icons.mic : Icons.mic_none,
            size: 50,
            color: Colors.white,
          ),
        ),
      ),
    );
  }
}

