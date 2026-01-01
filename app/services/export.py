"""
Conversation Export & Sharing Service
Exports conversations as PDF, text, JSON, or share links
"""
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

EXPORT_DIR = Path(__file__).parent.parent.parent / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


class ExportService:
    """
    Service for exporting and sharing conversations.
    Supports multiple export formats.
    """
    
    def __init__(self):
        self.exports = {}  # {export_id: export_info}
        logger.info("Export service initialized")
    
    def export_conversation(
        self,
        session_id: str,
        conversation_history: List[Dict],
        format: str = "json"
    ) -> Dict:
        """
        Export conversation in specified format.
        
        Args:
            session_id: Session identifier
            conversation_history: List of conversation messages
            format: Export format ("json", "text", "markdown")
        
        Returns:
            Dictionary with export data and metadata
        """
        export_id = f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format == "json":
            content = self._export_json(conversation_history)
            filename = f"{export_id}.json"
            mime_type = "application/json"
        
        elif format == "text":
            content = self._export_text(conversation_history)
            filename = f"{export_id}.txt"
            mime_type = "text/plain"
        
        elif format == "markdown":
            content = self._export_markdown(conversation_history)
            filename = f"{export_id}.md"
            mime_type = "text/markdown"
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Save export
        export_path = EXPORT_DIR / filename
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        export_info = {
            'export_id': export_id,
            'session_id': session_id,
            'format': format,
            'filename': filename,
            'path': str(export_path),
            'size': len(content),
            'created_at': datetime.now().isoformat(),
            'message_count': len(conversation_history)
        }
        
        self.exports[export_id] = export_info
        
        logger.info(f"Exported conversation: {export_id} ({format})")
        
        return {
            'export_id': export_id,
            'filename': filename,
            'content': content,
            'mime_type': mime_type,
            'metadata': export_info
        }
    
    def _export_json(self, conversation_history: List[Dict]) -> str:
        """Export as JSON"""
        export_data = {
            'conversation': conversation_history,
            'exported_at': datetime.now().isoformat(),
            'message_count': len(conversation_history)
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_text(self, conversation_history: List[Dict]) -> str:
        """Export as plain text"""
        lines = []
        lines.append("=" * 60)
        lines.append("CONVERSATION EXPORT")
        lines.append("=" * 60)
        lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Messages: {len(conversation_history)}")
        lines.append("=" * 60)
        lines.append("")
        
        for i, msg in enumerate(conversation_history, 1):
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            lines.append(f"[{i}] {role}:")
            lines.append(content)
            lines.append("")
        
        return "\n".join(lines)
    
    def _export_markdown(self, conversation_history: List[Dict]) -> str:
        """Export as Markdown"""
        lines = []
        lines.append("# Conversation Export")
        lines.append("")
        lines.append(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Messages:** {len(conversation_history)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        for i, msg in enumerate(conversation_history, 1):
            role = msg.get('role', 'unknown').title()
            content = msg.get('content', '')
            lines.append(f"## {i}. {role}")
            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_export(self, export_id: str) -> Optional[Dict]:
        """Get export information"""
        return self.exports.get(export_id)
    
    def list_exports(self, session_id: Optional[str] = None) -> List[Dict]:
        """List all exports, optionally filtered by session"""
        exports = list(self.exports.values())
        if session_id:
            exports = [e for e in exports if e['session_id'] == session_id]
        return exports
    
    def delete_export(self, export_id: str) -> bool:
        """Delete an export"""
        if export_id in self.exports:
            export_info = self.exports[export_id]
            export_path = Path(export_info['path'])
            if export_path.exists():
                export_path.unlink()
            del self.exports[export_id]
            logger.info(f"Deleted export: {export_id}")
            return True
        return False


# Global export service instance
_export_service = ExportService()


def get_export_service() -> ExportService:
    """Get global export service instance"""
    return _export_service

