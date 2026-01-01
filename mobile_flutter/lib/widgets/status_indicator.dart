import 'package:flutter/material.dart';

class StatusIndicator extends StatelessWidget {
  final bool isConnected;
  final String status;
  final bool isProcessing;

  const StatusIndicator({
    super.key,
    required this.isConnected,
    required this.status,
    required this.isProcessing,
  });

  @override
  Widget build(BuildContext context) {
    Color indicatorColor;
    if (isProcessing) {
      indicatorColor = Colors.orange;
    } else if (isConnected) {
      indicatorColor = Colors.green;
    } else {
      indicatorColor = Colors.red;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: indicatorColor,
              shape: BoxShape.circle,
            ),
            child: isProcessing
                ? const Center(
                    child: SizedBox(
                      width: 8,
                      height: 8,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    ),
                  )
                : null,
          ),
          const SizedBox(width: 8),
          Text(
            status,
            style: TextStyle(
              color: Colors.grey[800],
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

