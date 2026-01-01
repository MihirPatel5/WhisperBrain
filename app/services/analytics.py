"""
Analytics & Monitoring Service
Tracks usage, performance, errors, and user engagement
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Analytics storage (in production, use database)
ANALYTICS_DIR = Path(__file__).parent.parent.parent / "analytics"
ANALYTICS_DIR.mkdir(exist_ok=True)


class AnalyticsService:
    """
    Tracks analytics and monitoring data.
    Stores metrics for analysis and reporting.
    """
    
    def __init__(self):
        self.metrics = {
            'conversations': 0,
            'total_messages': 0,
            'total_audio_processed': 0,
            'errors': 0,
            'average_response_time': 0.0,
            'sessions': 0,
            'active_users': set(),
            'error_log': [],
            'performance_log': []
        }
        self._load_analytics()
        logger.info("Analytics service initialized")
    
    def _load_analytics(self):
        """Load analytics from storage"""
        analytics_file = ANALYTICS_DIR / "analytics.json"
        if analytics_file.exists():
            try:
                with open(analytics_file, "r") as f:
                    data = json.load(f)
                    self.metrics.update(data)
                    # Convert active_users back to set
                    if 'active_users' in data:
                        self.metrics['active_users'] = set(data['active_users'])
            except Exception as e:
                logger.warning(f"Failed to load analytics: {e}")
    
    def _save_analytics(self):
        """Save analytics to storage"""
        analytics_file = ANALYTICS_DIR / "analytics.json"
        try:
            # Convert set to list for JSON
            data = self.metrics.copy()
            data['active_users'] = list(data['active_users'])
            with open(analytics_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save analytics: {e}")
    
    def track_conversation(
        self,
        session_id: str,
        user_id: str,
        metrics: Dict
    ):
        """
        Track conversation metrics.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            metrics: Dictionary with metrics (duration, message_count, etc.)
        """
        self.metrics['conversations'] += 1
        self.metrics['total_messages'] += metrics.get('message_count', 1)
        self.metrics['sessions'] += 1
        self.metrics['active_users'].add(user_id)
        
        # Update average response time
        response_time = metrics.get('response_time', 0)
        if response_time > 0:
            current_avg = self.metrics['average_response_time']
            total = self.metrics['conversations']
            self.metrics['average_response_time'] = (
                (current_avg * (total - 1) + response_time) / total
            )
        
        # Track audio processed
        audio_size = metrics.get('audio_size', 0)
        self.metrics['total_audio_processed'] += audio_size
        
        self._save_analytics()
        logger.debug(f"Tracked conversation: {session_id}")
    
    def track_error(
        self,
        error_type: str,
        error_message: str,
        session_id: Optional[str] = None
    ):
        """Track errors"""
        self.metrics['errors'] += 1
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_message,
            'session_id': session_id
        }
        self.metrics['error_log'].append(error_entry)
        
        # Keep only last 100 errors
        if len(self.metrics['error_log']) > 100:
            self.metrics['error_log'] = self.metrics['error_log'][-100:]
        
        self._save_analytics()
        logger.warning(f"Tracked error: {error_type} - {error_message}")
    
    def track_performance(
        self,
        operation: str,
        duration: float,
        session_id: Optional[str] = None
    ):
        """Track performance metrics"""
        perf_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration': duration,
            'session_id': session_id
        }
        self.metrics['performance_log'].append(perf_entry)
        
        # Keep only last 100 performance entries
        if len(self.metrics['performance_log']) > 100:
            self.metrics['performance_log'] = self.metrics['performance_log'][-100:]
        
        self._save_analytics()
        logger.debug(f"Tracked performance: {operation} - {duration:.2f}s")
    
    def get_stats(self) -> Dict:
        """Get analytics statistics"""
        return {
            'conversations': self.metrics['conversations'],
            'total_messages': self.metrics['total_messages'],
            'total_audio_processed': self.metrics['total_audio_processed'],
            'errors': self.metrics['errors'],
            'average_response_time': self.metrics['average_response_time'],
            'sessions': self.metrics['sessions'],
            'active_users_count': len(self.metrics['active_users']),
            'error_rate': (
                self.metrics['errors'] / max(self.metrics['conversations'], 1)
            ) * 100
        }
    
    def get_error_log(self, limit: int = 10) -> List[Dict]:
        """Get recent error log"""
        return self.metrics['error_log'][-limit:]
    
    def get_performance_log(self, limit: int = 10) -> List[Dict]:
        """Get recent performance log"""
        return self.metrics['performance_log'][-limit:]


# Global analytics instance
_analytics_service = AnalyticsService()


def get_analytics() -> AnalyticsService:
    """Get global analytics service instance"""
    return _analytics_service

