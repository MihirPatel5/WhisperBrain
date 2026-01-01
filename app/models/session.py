"""
Session Management Models
Handles user sessions and conversation tracking
"""
from datetime import datetime
from typing import List, Dict, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class UserSession:
    """
    Represents a user session with conversation history.
    Each WebSocket connection gets a unique session.
    """
    
    def __init__(self, session_id: Optional[str] = None, user_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id or f"user_{uuid.uuid4().hex[:8]}"
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.conversation_count = 0
        self.is_active = True
        
        logger.info(f"Created session: {self.session_id} for user: {self.user_id}")
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def increment_conversation(self):
        """Increment conversation count"""
        self.conversation_count += 1
        self.update_activity()
    
    def deactivate(self):
        """Mark session as inactive"""
        self.is_active = False
        logger.info(f"Session {self.session_id} deactivated")
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'conversation_count': self.conversation_count,
            'is_active': self.is_active
        }


class SessionManager:
    """
    Manages multiple user sessions.
    Tracks active sessions and handles cleanup.
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        self.sessions: Dict[str, UserSession] = {}
        self.session_timeout_minutes = session_timeout_minutes
        logger.info(f"Session manager initialized with {session_timeout_minutes}min timeout")
    
    def create_session(self, session_id: Optional[str] = None, user_id: Optional[str] = None) -> UserSession:
        """Create a new session"""
        session = UserSession(session_id, user_id)
        self.sessions[session.session_id] = session
        logger.info(f"Created session: {session.session_id}, total sessions: {len(self.sessions)}")
        return session
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
        return session
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> UserSession:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session.update_activity()
            return session
        return self.create_session(session_id)
    
    def remove_session(self, session_id: str):
        """Remove a session"""
        if session_id in self.sessions:
            self.sessions[session_id].deactivate()
            del self.sessions[session_id]
            logger.info(f"Removed session: {session_id}, remaining: {len(self.sessions)}")
    
    def cleanup_inactive_sessions(self):
        """Remove sessions that have been inactive too long"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
        inactive = [
            sid for sid, session in self.sessions.items()
            if session.last_activity < cutoff_time
        ]
        
        for sid in inactive:
            self.remove_session(sid)
        
        if inactive:
            logger.info(f"Cleaned up {len(inactive)} inactive sessions")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len([s for s in self.sessions.values() if s.is_active])
    
    def get_stats(self) -> Dict:
        """Get session manager statistics"""
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': self.get_active_sessions_count(),
            'session_timeout_minutes': self.session_timeout_minutes
        }

