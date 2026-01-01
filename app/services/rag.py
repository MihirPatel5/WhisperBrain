"""
RAG (Retrieval Augmented Generation) Service
Provides context from knowledge base to enhance LLM responses
"""
import logging
from typing import List, Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Knowledge base storage
KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)


class RAGService:
    """
    Retrieval Augmented Generation service.
    Retrieves relevant context from knowledge base.
    """
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.knowledge_base = {}  # Simple in-memory storage
        self._load_knowledge_base()
        logger.info(f"RAG service initialized (enabled: {enabled})")
    
    def _load_knowledge_base(self):
        """Load knowledge base from storage"""
        knowledge_file = KNOWLEDGE_BASE_DIR / "knowledge.json"
        if knowledge_file.exists():
            try:
                with open(knowledge_file, "r", encoding="utf-8") as f:
                    self.knowledge_base = json.load(f)
                logger.info(f"Loaded {len(self.knowledge_base)} knowledge entries")
            except Exception as e:
                logger.warning(f"Failed to load knowledge base: {e}")
    
    def _save_knowledge_base(self):
        """Save knowledge base to storage"""
        knowledge_file = KNOWLEDGE_BASE_DIR / "knowledge.json"
        try:
            with open(knowledge_file, "w", encoding="utf-8") as f:
                json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save knowledge base: {e}")
    
    def add_knowledge(
        self,
        topic: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        Add knowledge to the knowledge base.
        
        Args:
            topic: Topic/keyword
            content: Knowledge content
            metadata: Optional metadata
        """
        if topic not in self.knowledge_base:
            self.knowledge_base[topic] = []
        
        entry = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        
        self.knowledge_base[topic].append(entry)
        self._save_knowledge_base()
        logger.info(f"Added knowledge for topic: {topic}")
    
    def retrieve_context(
        self,
        query: str,
        max_results: int = 3
    ) -> List[str]:
        """
        Retrieve relevant context from knowledge base.
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of relevant context strings
        """
        if not self.enabled:
            return []
        
        if not self.knowledge_base:
            return []
        
        query_lower = query.lower()
        results = []
        
        # Simple keyword matching (in production, use vector search)
        for topic, entries in self.knowledge_base.items():
            if topic.lower() in query_lower or query_lower in topic.lower():
                for entry in entries[:max_results]:
                    results.append(entry["content"])
                    if len(results) >= max_results:
                        break
                if len(results) >= max_results:
                    break
        
        # Also search in content
        if len(results) < max_results:
            for topic, entries in self.knowledge_base.items():
                for entry in entries:
                    if query_lower in entry["content"].lower():
                        if entry["content"] not in results:
                            results.append(entry["content"])
                            if len(results) >= max_results:
                                break
                if len(results) >= max_results:
                    break
        
        logger.info(f"Retrieved {len(results)} context entries for query: {query[:50]}")
        return results
    
    def get_knowledge_stats(self) -> Dict[str, any]:
        """Get statistics about knowledge base"""
        total_entries = sum(len(entries) for entries in self.knowledge_base.values())
        return {
            'enabled': self.enabled,
            'topics': len(self.knowledge_base),
            'total_entries': total_entries,
            'topics_list': list(self.knowledge_base.keys())
        }


# Global RAG service instance
_rag_service = RAGService(enabled=False)


def get_rag_service() -> RAGService:
    """Get global RAG service instance"""
    return _rag_service

