"""
Emotion & Sentiment Detection Service
Detects emotion in user voice and text for empathetic responses
"""
import logging
import re
from typing import Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EmotionDetector:
    """
    Detects emotion from audio prosody and text sentiment.
    Provides emotion-aware responses.
    """
    
    def __init__(self):
        # Emotion keywords
        self.emotion_keywords = {
            'happy': ['happy', 'joy', 'excited', 'great', 'wonderful', 'amazing', 'love', '😊', '😄'],
            'sad': ['sad', 'depressed', 'unhappy', 'down', 'upset', 'crying', '😢', '😞'],
            'angry': ['angry', 'mad', 'furious', 'annoyed', 'frustrated', '😠', '😡'],
            'fearful': ['scared', 'afraid', 'worried', 'anxious', 'nervous', '😰', '😨'],
            'surprised': ['surprised', 'shocked', 'wow', 'unexpected', '😲', '😮'],
            'neutral': ['okay', 'fine', 'alright', 'sure', 'yes', 'no']
        }
        
        # Sentiment patterns
        self.positive_patterns = [
            r'\b(good|great|excellent|wonderful|amazing|fantastic|love|like|enjoy)\b',
            r'\b(thank|thanks|appreciate|grateful)\b',
            r'\b(yes|yeah|yep|sure|okay|ok)\b'
        ]
        
        self.negative_patterns = [
            r'\b(bad|terrible|awful|hate|dislike|horrible|worst)\b',
            r'\b(no|nope|nah|not|don\'t|can\'t|won\'t)\b',
            r'\b(problem|issue|error|wrong|broken|failed)\b'
        ]
        
        logger.info("Emotion detector initialized")
    
    def detect_emotion_from_text(self, text: str) -> Dict[str, any]:
        """
        Detect emotion from text using keyword matching and sentiment analysis.
        
        Args:
            text: User's text input
        
        Returns:
            Dictionary with emotion, sentiment, confidence, and suggestions
        """
        text_lower = text.lower()
        
        # Count emotion keywords
        emotion_scores = {}
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        # Detect sentiment
        positive_count = sum(1 for pattern in self.positive_patterns if re.search(pattern, text_lower, re.IGNORECASE))
        negative_count = sum(1 for pattern in self.negative_patterns if re.search(pattern, text_lower, re.IGNORECASE))
        
        # Determine primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[primary_emotion] / max(len(text.split()), 1)
        else:
            # Default to sentiment-based emotion
            if positive_count > negative_count:
                primary_emotion = 'happy'
                confidence = 0.6
            elif negative_count > positive_count:
                primary_emotion = 'sad'
                confidence = 0.6
            else:
                primary_emotion = 'neutral'
                confidence = 0.5
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Generate response suggestions
        suggestions = self._get_response_suggestions(primary_emotion, sentiment)
        
        result = {
            'emotion': primary_emotion,
            'sentiment': sentiment,
            'confidence': min(confidence, 1.0),
            'suggestions': suggestions,
            'emotion_scores': emotion_scores
        }
        
        logger.info(f"Detected emotion: {primary_emotion} ({sentiment}), confidence: {confidence:.2f}")
        return result
    
    def detect_emotion_from_audio(self, audio_bytes: bytes) -> Dict[str, any]:
        """
        Detect emotion from audio prosody (pitch, energy, tempo).
        
        Args:
            audio_bytes: Audio data in WAV format
        
        Returns:
            Dictionary with emotion detected from audio features
        """
        # Placeholder: In production, use audio analysis libraries
        # For now, return neutral (requires audio processing libraries)
        
        # Simple heuristic: longer audio might indicate more emotion
        audio_length = len(audio_bytes)
        
        # Placeholder analysis
        # In production, analyze:
        # - Pitch variation (higher = excited/angry, lower = sad)
        # - Energy level (higher = happy/angry, lower = sad)
        # - Speech rate (faster = excited/angry, slower = sad)
        
        return {
            'emotion': 'neutral',
            'confidence': 0.5,
            'audio_length': audio_length,
            'note': 'Audio emotion detection requires audio processing libraries'
        }
    
    def detect_emotion(self, text: Optional[str] = None, audio_bytes: Optional[bytes] = None) -> Dict[str, any]:
        """
        Detect emotion from text and/or audio.
        
        Args:
            text: User's text input (optional)
            audio_bytes: Audio data (optional)
        
        Returns:
            Combined emotion detection result
        """
        results = {}
        
        if text:
            text_result = self.detect_emotion_from_text(text)
            results['text'] = text_result
            results['primary'] = text_result
        
        if audio_bytes:
            audio_result = self.detect_emotion_from_audio(audio_bytes)
            results['audio'] = audio_result
            
            # Combine results if both available
            if text:
                # Weight text more heavily (more reliable)
                results['primary'] = text_result
                results['audio_secondary'] = audio_result
            else:
                results['primary'] = audio_result
        
        if not results:
            # Default to neutral
            results['primary'] = {
                'emotion': 'neutral',
                'sentiment': 'neutral',
                'confidence': 0.5
            }
        
        return results
    
    def _get_response_suggestions(self, emotion: str, sentiment: str) -> Dict[str, str]:
        """Get suggestions for emotion-aware responses"""
        suggestions = {
            'tone': 'neutral',
            'style': 'professional',
            'empathy': False
        }
        
        if emotion == 'happy' or sentiment == 'positive':
            suggestions['tone'] = 'enthusiastic'
            suggestions['style'] = 'friendly'
            suggestions['empathy'] = True
        
        elif emotion == 'sad' or sentiment == 'negative':
            suggestions['tone'] = 'supportive'
            suggestions['style'] = 'empathetic'
            suggestions['empathy'] = True
        
        elif emotion == 'angry':
            suggestions['tone'] = 'calm'
            suggestions['style'] = 'patient'
            suggestions['empathy'] = True
        
        elif emotion == 'fearful':
            suggestions['tone'] = 'reassuring'
            suggestions['style'] = 'gentle'
            suggestions['empathy'] = True
        
        return suggestions


class SentimentAnalyzer:
    """
    Analyzes text sentiment (positive, negative, neutral).
    """
    
    def analyze(self, text: str) -> Dict[str, any]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Sentiment analysis result
        """
        detector = EmotionDetector()
        result = detector.detect_emotion_from_text(text)
        
        return {
            'sentiment': result['sentiment'],
            'confidence': result['confidence'],
            'emotion': result['emotion']
        }

