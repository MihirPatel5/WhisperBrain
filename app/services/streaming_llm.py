"""
Streaming LLM Service
Streams LLM responses word-by-word for better UX
"""
import subprocess
import logging
import re
import requests
import json
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Try smaller models first
MODELS = ["tinyllama", "phi3:mini", "llama3.2:1b", "llama3.2", "phi3"]
OLLAMA_API_URL = "http://localhost:11434/api/chat"


async def stream_llm_response(
    prompt: str,
    conversation_history: list = None,
    model: str = None
) -> AsyncGenerator[str, None]:
    """
    Stream LLM response word-by-word.
    
    Args:
        prompt: User's question
        conversation_history: Previous conversation (optional)
        model: Specific model to use (optional)
    
    Yields:
        Text chunks as they're generated
    """
    from datetime import datetime
    
    current_date = datetime.now().strftime("%B %d, %Y")
    current_day = datetime.now().strftime("%A")
    
    # Build messages for streaming
    messages = []
    
    # System message
    messages.append({
        "role": "system",
        "content": f"""Today is {current_date} ({current_day}).

CRITICAL RULES:
1. Answer ONLY the current question asked by the user
2. Do NOT repeat, summarize, or reference previous conversations
3. Do NOT include previous questions or answers in your response
4. Be direct, concise, and focused on the current question only
5. If the user asks about something, answer that specific thing - nothing else"""
    })
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
    
    # Add current question
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Try streaming with Ollama API
    models_to_try = [model] if model else MODELS
    
    for model_name in models_to_try:
        try:
            logger.info(f"Trying streaming with model: {model_name}")
            
            # Stream from Ollama API
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": model_name,
                    "messages": messages,
                    "stream": True,  # Enable streaming
                    "options": {
                        "temperature": 0.7,
                    }
                },
                stream=True,
                timeout=120
            )
            
            if response.status_code == 200:
                # Stream the response
                buffer = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            if 'message' in chunk_data and 'content' in chunk_data['message']:
                                content = chunk_data['message']['content']
                                if content:
                                    buffer += content
                                    # Yield accumulated content
                                    yield content
                                
                                # Check if done
                                if chunk_data.get('done', False):
                                    break
                        except json.JSONDecodeError:
                            continue
                
                if buffer:
                    logger.info(f"Streamed response from {model_name}: {len(buffer)} chars")
                    return
            else:
                logger.warning(f"Streaming API failed with status {response.status_code}, trying next model")
                continue
                
        except (requests.exceptions.RequestException, KeyError) as e:
            logger.info(f"Streaming API not available or failed: {e}, trying next model")
            continue
    
    # Fallback: Return full response (non-streaming)
    logger.warning("Streaming not available, falling back to non-streaming")
    from app.llm import chat_with_llm
    full_response = chat_with_llm(prompt, conversation_history)
    yield full_response

