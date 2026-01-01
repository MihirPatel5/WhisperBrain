"""
Webhook Integration Service
Sends conversation events to external services
"""
import logging
import requests
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Service for sending webhooks to external services.
    Supports multiple webhook URLs and event types.
    """
    
    def __init__(self):
        self.webhooks: Dict[str, List[str]] = {}  # {event_type: [urls]}
        self.enabled = True
        logger.info("Webhook service initialized")
    
    def register_webhook(
        self,
        event_type: str,
        url: str
    ):
        """
        Register a webhook URL for an event type.
        
        Args:
            event_type: Type of event (e.g., 'conversation_start', 'message', 'error')
            url: Webhook URL to call
        """
        if event_type not in self.webhooks:
            self.webhooks[event_type] = []
        
        if url not in self.webhooks[event_type]:
            self.webhooks[event_type].append(url)
            logger.info(f"Registered webhook: {event_type} -> {url}")
    
    def unregister_webhook(
        self,
        event_type: str,
        url: str
    ):
        """Unregister a webhook URL"""
        if event_type in self.webhooks and url in self.webhooks[event_type]:
            self.webhooks[event_type].remove(url)
            logger.info(f"Unregistered webhook: {event_type} -> {url}")
    
    async def send_webhook(
        self,
        event_type: str,
        data: Dict,
        timeout: int = 5
    ):
        """
        Send webhook for an event.
        
        Args:
            event_type: Type of event
            data: Data to send
            timeout: Request timeout in seconds
        """
        if not self.enabled:
            return
        
        if event_type not in self.webhooks:
            return
        
        urls = self.webhooks[event_type]
        if not urls:
            return
        
        # Prepare payload
        payload = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Send to all registered URLs
        tasks = []
        for url in urls:
            task = self._send_webhook_request(url, payload, timeout)
            tasks.append(task)
        
        # Execute all webhooks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.warning(f"Webhook failed for {url}: {result}")
            else:
                logger.debug(f"Webhook sent to {url}")
    
    async def _send_webhook_request(
        self,
        url: str,
        payload: Dict,
        timeout: int
    ):
        """Send HTTP POST request to webhook URL"""
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Webhook request failed for {url}: {e}")
            raise
    
    def get_registered_webhooks(self) -> Dict[str, List[str]]:
        """Get all registered webhooks"""
        return self.webhooks.copy()


# Global webhook service instance
_webhook_service = WebhookService()


def get_webhook_service() -> WebhookService:
    """Get global webhook service instance"""
    return _webhook_service

