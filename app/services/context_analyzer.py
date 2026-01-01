"""
Context Relevance Analyzer
Determines when previous conversation context is actually needed
"""
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """
    Analyzes if current question needs previous context.
    Only includes context when it's actually relevant.
    """
    
    def __init__(self):
        # Keywords that indicate context is needed
        self.context_keywords = [
            'it', 'that', 'this', 'them', 'those', 'these',
            'what about', 'how about', 'and', 'also', 'too',
            'previous', 'earlier', 'before', 'mentioned', 'said',
            'same', 'similar', 'like that', 'as well',
            'follow up', 'continue', 'more', 'else',
            'what else', 'anything else', 'other', 'another'
        ]
        
        # Patterns that indicate standalone questions (no context needed)
        self.standalone_patterns = [
            r'^what is\s+',           # "What is Python?"
            r'^what are\s+',          # "What are functions?"
            r'^who is\s+',            # "Who is Einstein?"
            r'^where is\s+',          # "Where is Paris?"
            r'^when did\s+',          # "When did WW2 end?"
            r'^how do\s+',            # "How do I install Python?"
            r'^tell me about\s+',     # "Tell me about AI"
            r'^explain\s+',           # "Explain quantum computing"
            r'^define\s+',            # "Define recursion"
            r'^describe\s+',         # "Describe the process"
        ]
        
        logger.info("Context analyzer initialized")
    
    def needs_context(self, current_question: str, conversation_history: List[Dict]) -> bool:
        """
        Determine if current question needs previous context.
        
        Args:
            current_question: The current user question
            conversation_history: Previous conversation messages
            
        Returns:
            True if context is needed, False if question is standalone
        """
        # No history = no context needed
        if not conversation_history or len(conversation_history) == 0:
            return False
        
        question_lower = current_question.lower().strip()
        question_with_spaces = f' {question_lower} '
        
        # FIRST: Check for reference words (highest priority)
        # If question has "it", "that", "this", etc., it likely needs context
        reference_words = [' it ', ' that ', ' this ', ' them ', ' those ', ' these ', ' they ', ' its ', ' their ']
        has_reference_word = any(ref in question_with_spaces for ref in reference_words)
        
        if has_reference_word:
            logger.debug(f"Reference word detected in: '{current_question[:50]}...' - context needed")
            return True
        
        # SECOND: Check for follow-up indicators
        if self._is_follow_up(question_lower):
            logger.debug(f"Follow-up question detected - context needed")
            return True
        
        # THIRD: Check if question references previous conversation (topic overlap)
        if self._references_previous(question_lower, conversation_history):
            logger.debug(f"Question references previous conversation - context needed")
            return True
        
        # FOURTH: Check if it's a standalone question (doesn't need context)
        if self._is_standalone_question(question_lower):
            logger.debug(f"Standalone question detected: '{current_question[:50]}...' - no context needed")
            return False
        
        # Default: standalone question, no context needed
        logger.debug(f"Standalone question - no context needed")
        return False
    
    def _is_standalone_question(self, question: str) -> bool:
        """Check if question is standalone (doesn't need context)"""
        question_lower = question.lower()
        
        # Check standalone patterns
        for pattern in self.standalone_patterns:
            if re.match(pattern, question_lower, re.IGNORECASE):
                return True
        return False
    
    def _references_previous(self, question: str, history: List[Dict]) -> bool:
        """Check if question references previous conversation"""
        # Strong reference indicators (definitely need context)
        # Check for pronouns and reference words
        strong_references = [' it ', ' that ', ' this ', ' them ', ' those ', ' these ', ' they ']
        question_with_spaces = f' {question.lower()} '
        
        has_strong_reference = any(ref in question_with_spaces for ref in strong_references)
        
        # Also check for references at start/end
        question_lower = question.lower()
        if question_lower.startswith('what is it') or question_lower.startswith('how do i') and ' it' in question_lower:
            has_strong_reference = True
        
        if has_strong_reference:
            return True
        
        # Check for reference keywords in context
        has_reference = any(keyword in question for keyword in self.context_keywords)
        
        if not has_reference:
            return False
        
        # Check if question actually relates to previous topics
        # Get last few messages to check topic overlap
        recent_topics = self._extract_topics(history[-4:])
        question_topics = self._extract_topics_from_text(question)
        
        # If there's topic overlap, likely needs context
        if recent_topics and question_topics:
            overlap = set(recent_topics) & set(question_topics)
            if overlap:
                return True
        
        return has_reference
    
    def _is_follow_up(self, question: str) -> bool:
        """Check if question is a follow-up to previous conversation"""
        follow_up_indicators = [
            'what about', 'how about', 'and', 'also', 'too',
            'what else', 'anything else', 'more about', 'tell me more',
            'continue', 'go on', 'keep going'
        ]
        
        return any(indicator in question for indicator in follow_up_indicators)
    
    def _extract_topics(self, messages: List[Dict]) -> List[str]:
        """Extract key topics from messages (simple keyword extraction)"""
        topics = []
        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                       'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                       'can', 'could', 'should', 'may', 'might', 'this', 'that',
                       'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
        
        for msg in messages:
            content = msg.get('content', '').lower()
            # Extract significant words (nouns, important terms)
            words = re.findall(r'\b[a-z]{4,}\b', content)
            # Filter out common words
            significant = [w for w in words if w not in common_words]
            topics.extend(significant[:5])  # Top 5 words per message
        
        return topics
    
    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract topics from a single text"""
        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                       'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                       'can', 'could', 'should', 'may', 'might', 'this', 'that',
                       'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                       'what', 'where', 'when', 'who', 'how', 'why'}
        
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        significant = [w for w in words if w not in common_words]
        return significant[:5]
    
    def get_relevant_context(self, current_question: str, conversation_history: List[Dict], max_messages: int = 2) -> Optional[List[Dict]]:
        """
        Get only relevant context if needed, otherwise return None.
        
        Args:
            current_question: Current user question
            conversation_history: Full conversation history
            max_messages: Maximum messages to include (default: 2 = 1 exchange)
            
        Returns:
            Relevant context messages or None if not needed
        """
        if not self.needs_context(current_question, conversation_history):
            return None
        
        # Only return the most recent exchange if context is needed
        if len(conversation_history) >= max_messages:
            return conversation_history[-max_messages:]
        else:
            return conversation_history

