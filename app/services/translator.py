"""
Real-time Translation Service
Translates conversations in real-time for cross-language communication
"""
import logging
import subprocess
import requests
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Translation service configuration
USE_LLM_TRANSLATION = True  # Use LLM for translation (more accurate)
FALLBACK_TO_API = False     # Fallback to translation API if LLM fails


class Translator:
    """
    Real-time translation service.
    Supports multiple translation methods.
    """
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese'
        }
        logger.info("Translator initialized")
    
    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Optional[str]:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'es', 'fr')
            source_language: Source language code (optional, auto-detect if None)
        
        Returns:
            Translated text or None if failed
        """
        if not text or not text.strip():
            return text
        
        if target_language not in self.supported_languages:
            logger.warning(f"Unsupported target language: {target_language}")
            return None
        
        # Try LLM translation first (more accurate)
        if USE_LLM_TRANSLATION:
            translated = self._translate_with_llm(text, target_language, source_language)
            if translated:
                return translated
        
        # Fallback to API translation
        if FALLBACK_TO_API:
            translated = self._translate_with_api(text, target_language, source_language)
            if translated:
                return translated
        
        logger.warning(f"Translation failed for: {text[:50]}...")
        return None
    
    def _translate_with_llm(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Optional[str]:
        """
        Translate using LLM (Ollama).
        More accurate and context-aware.
        """
        try:
            import subprocess
            
            target_lang_name = self.supported_languages.get(target_language, target_language)
            
            # Build translation prompt
            if source_language:
                source_lang_name = self.supported_languages.get(source_language, source_language)
                prompt = f"Translate the following text from {source_lang_name} to {target_lang_name}. Only return the translation, nothing else:\n\n{text}"
            else:
                prompt = f"Translate the following text to {target_lang_name}. Only return the translation, nothing else:\n\n{text}"
            
            # Use Ollama for translation
            models = ["tinyllama", "phi3:mini", "llama3.2:1b", "llama3.2"]
            
            for model in models:
                try:
                    result = subprocess.run(
                        ["ollama", "run", model],
                        input=prompt.encode(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=30,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        translated = result.stdout.decode().strip()
                        # Clean up response
                        translated = translated.replace(prompt, "").strip()
                        translated = translated.split('\n')[0].strip()
                        
                        if translated and len(translated) > 0:
                            logger.info(f"Translated via LLM: {text[:30]}... -> {translated[:30]}...")
                            return translated
                except Exception as e:
                    logger.debug(f"LLM translation failed with {model}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"LLM translation error: {e}")
            return None
    
    def _translate_with_api(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Optional[str]:
        """
        Translate using external API (e.g., Google Translate API).
        Requires API key configuration.
        """
        # Placeholder for API translation
        # In production, integrate with translation API
        logger.info("API translation not configured")
        return None
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Language code or None
        """
        # Simple language detection using keywords
        text_lower = text.lower()
        
        # Spanish indicators
        if any(word in text_lower for word in ['hola', 'gracias', 'por favor', 'cómo', 'qué']):
            return 'es'
        
        # French indicators
        if any(word in text_lower for word in ['bonjour', 'merci', 's\'il vous plaît', 'comment']):
            return 'fr'
        
        # German indicators
        if any(word in text_lower for word in ['hallo', 'danke', 'bitte', 'wie']):
            return 'de'
        
        # Default to English
        return 'en'
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()


async def translate_conversation(
    text: str,
    target_language: str,
    source_language: Optional[str] = None
) -> Optional[str]:
    """
    Async wrapper for translation.
    
    Args:
        text: Text to translate
        target_language: Target language code
        source_language: Source language code (optional)
    
    Returns:
        Translated text
    """
    translator = Translator()
    return translator.translate_text(text, target_language, source_language)

