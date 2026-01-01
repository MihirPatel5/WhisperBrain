"""
User Preferences Service
Manages user preferences and settings storage
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Preferences storage directory
PREFERENCES_DIR = Path(__file__).parent.parent.parent / "user_preferences"
PREFERENCES_DIR.mkdir(exist_ok=True)


class UserPreferences:
    """
    Manages user preferences storage and retrieval.
    """
    
    def __init__(self):
        self.preferences_file = PREFERENCES_DIR / "preferences.json"
        self.preferences = self._load_preferences()
        logger.info("User preferences service initialized")
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load preferences from storage"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load preferences: {e}")
                return self._get_default_preferences()
        return self._get_default_preferences()
    
    def _save_preferences(self):
        """Save preferences to storage"""
        try:
            with open(self.preferences_file, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
            logger.debug("Preferences saved successfully")
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default preferences"""
        return {
            "audio": {
                "sample_rate": 16000,
                "quality": "medium",  # low, medium, high
                "format": "wav"
            },
            "ui": {
                "theme": "light",  # light, dark, auto
                "language": "en",
                "animations": True
            },
            "llm": {
                "default_model": "phi3:mini",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "features": {
                "vad_enabled": True,
                "emotion_detection": True,
                "translation": False,
                "rag_enabled": False,
                "tools_enabled": False
            },
            "connection": {
                "auto_reconnect": True,
                "reconnect_delay": 3,  # seconds
                "max_retries": 5
            },
            "updated_at": datetime.now().isoformat()
        }
    
    def get_preference(self, category: str, key: str, default: Any = None) -> Any:
        """
        Get a specific preference value.
        
        Args:
            category: Preference category (e.g., 'audio', 'ui')
            key: Preference key (e.g., 'theme', 'sample_rate')
            default: Default value if not found
        
        Returns:
            Preference value or default
        """
        return self.preferences.get(category, {}).get(key, default)
    
    def set_preference(self, category: str, key: str, value: Any):
        """
        Set a preference value.
        
        Args:
            category: Preference category
            key: Preference key
            value: Preference value
        """
        if category not in self.preferences:
            self.preferences[category] = {}
        
        self.preferences[category][key] = value
        self.preferences["updated_at"] = datetime.now().isoformat()
        self._save_preferences()
        logger.info(f"Preference updated: {category}.{key} = {value}")
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all preferences"""
        return self.preferences.copy()
    
    def update_preferences(self, updates: Dict[str, Any]):
        """
        Update multiple preferences at once.
        
        Args:
            updates: Dictionary of category -> {key: value} updates
        """
        for category, values in updates.items():
            if category not in self.preferences:
                self.preferences[category] = {}
            
            if isinstance(values, dict):
                self.preferences[category].update(values)
            else:
                self.preferences[category] = values
        
        self.preferences["updated_at"] = datetime.now().isoformat()
        self._save_preferences()
        logger.info(f"Preferences updated: {len(updates)} categories")
    
    def reset_to_defaults(self):
        """Reset all preferences to defaults"""
        self.preferences = self._get_default_preferences()
        self._save_preferences()
        logger.info("Preferences reset to defaults")
    
    def get_user_preferences_for_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get preferences for a specific user (or default if no user).
        
        Args:
            user_id: Optional user ID
        
        Returns:
            User preferences
        """
        # For now, return global preferences
        # In future, can support per-user preferences
        return self.get_all_preferences()


# Global preferences instance
_preferences = UserPreferences()


def get_user_preferences() -> UserPreferences:
    """Get global user preferences instance"""
    return _preferences

