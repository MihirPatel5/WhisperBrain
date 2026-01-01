import subprocess
import logging
import re
import json
import requests

logger = logging.getLogger(__name__)

# Try smaller models first - ordered by size (smallest first)
MODELS = ["tinyllama", "phi3:mini", "llama3.2:1b", "llama3.2", "phi3"]
OLLAMA_API_URL = "http://localhost:11434/api/chat"


def get_model_for_query(model_preference: str = None, use_case: str = None, text: str = None) -> str:
    """
    Get model to use for query (supports model selection).
    
    Args:
        model_preference: Preferred model (optional)
        use_case: Use case (optional)
        text: User text (optional)
    
    Returns:
        Model name
    """
    if model_preference and model_preference in MODELS:
        return model_preference
    
    # Use model selector if available
    try:
        from app.services.model_selector import get_model_selector
        selector = get_model_selector()
        return selector.select_model(use_case=use_case, text=text, user_preference=model_preference)
    except Exception:
        # Fallback to default
        return MODELS[1] if len(MODELS) > 1 else MODELS[0]


def _clean_response(response: str) -> str:
    """Clean LLM response to remove repetition and unwanted content"""
    import re
    
    # Remove script-like content
    response = re.sub(r'\[CUT TO:.*?\]', '', response, flags=re.IGNORECASE | re.DOTALL)
    response = re.sub(r'NARRATOR.*?:', '', response, flags=re.IGNORECASE | re.DOTALL)
    response = re.sub(r'INT\.|EXT\.', '', response, flags=re.IGNORECASE)
    
    # Remove references to previous conversations
    response = re.sub(r'previous.*?conversation.*?:', '', response, flags=re.IGNORECASE)
    response = re.sub(r'as.*?discussed.*?:', '', response, flags=re.IGNORECASE)
    response = re.sub(r'earlier.*?:', '', response, flags=re.IGNORECASE)
    response = re.sub(r'based on.*?previous.*?:', '', response, flags=re.IGNORECASE)
    
    # Remove verbose prefixes
    verbose_patterns = [
        r'certainly!.*?:',
        r'here is.*?:',
        r'let me.*?:',
    ]
    for pattern in verbose_patterns:
        response = re.sub(pattern, '', response, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up whitespace
    response = re.sub(r'\s+', ' ', response).strip()
    
    return response


def chat_with_llm(
    prompt: str,
    conversation_history: list = None,
    model_preference: str = None,
    use_case: str = None,
    rag_context: list = None
) -> str:
    """
    Chat with LLM with enhanced features.
    
    Args:
        prompt: User prompt
        conversation_history: Conversation history
        model_preference: Preferred model (optional)
        use_case: Use case for model selection (optional)
        rag_context: RAG context from knowledge base (optional)
    """
    # Select model
    selected_model = get_model_for_query(model_preference, use_case, prompt)
    
    # Add RAG context to prompt if available
    if rag_context and len(rag_context) > 0:
        context_text = "\n\nRelevant context from knowledge base:\n"
        context_text += "\n".join(f"- {ctx}" for ctx in rag_context[:3])  # Limit to 3 contexts
        prompt = prompt + context_text
    
    last_error = None
    
    # Add system prompt for better responses with current date
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    current_day = datetime.now().strftime("%A")
    
    # Build prompt - minimize context to prevent repetition
    # For CLI fallback, use minimal or no context
    if conversation_history and len(conversation_history) > 0:
        # Only use context if absolutely necessary (e.g., follow-up questions)
        # For most cases, answer without context to avoid repetition
        full_prompt = f"""Answer this question directly and briefly: {prompt}

Today's date: {current_date} ({current_day}).

CRITICAL: Answer ONLY this question. Do NOT repeat, summarize, or reference any previous conversations. Be direct and focused."""
    else:
        # First message - no context needed
        full_prompt = f"""Answer this question directly and briefly: {prompt}

Today's date: {current_date} ({current_day}).

Be concise and helpful."""
    
    # Try selected model first, then fallback to others
    models_to_try = [selected_model] + [m for m in MODELS if m != selected_model]
    
    for model in models_to_try:
        try:
            logger.info(f"Trying model: {model}")
            
            # Build messages for chat API
            messages = []
            
            # Add system message with date - VERY STRICT about not repeating
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
            
            # Add conversation history ONLY if provided (context analyzer determines if needed)
            # Context is only included when question actually references previous conversation
            if conversation_history and len(conversation_history) > 0:
                # Context analyzer has already determined this is needed
                # Only include the relevant context (usually just last exchange)
                for msg in conversation_history:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
                logger.debug(f"Including {len(conversation_history)} context messages")
            else:
                # No context - standalone question
                logger.debug("No context included - standalone question")
            
            # Add current question
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Try API first
            try:
                response_data = requests.post(
                    OLLAMA_API_URL,
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 200,  # Limit response length
                        }
                    },
                    timeout=120
                )
                
                if response_data.status_code == 200:
                    result = response_data.json()
                    response = result.get('message', {}).get('content', '').strip()
                    
                    if response:
                        # Clean response to remove any repetition
                        response = _clean_response(response)
                        logger.info(f"Successfully got response from {model} via API")
                        return response
                else:
                    logger.warning(f"API request failed with status {response_data.status_code}, trying CLI")
            except (requests.exceptions.RequestException, KeyError) as e:
                logger.info(f"API not available or failed: {e}, trying CLI method")
            
            # Fallback to CLI
            result = subprocess.run(
                ["ollama", "run", model],
                input=full_prompt.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=120,
            )
            response = result.stdout.decode().strip()
            # Filter out ANSI escape codes and progress indicators
            response = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', response)
            response = re.sub(r'[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]', '', response)
            response = response.strip()
            
            # Clean up verbose responses and remove repetition
            if response:
                # Remove common verbose prefixes
                verbose_prefixes = [
                    r'certainly!.*?answer:',
                    r'here is.*?answer:',
                    r'previous conversation.*?answer:',
                    r'context.*?answer:',
                    r'based on.*?previous.*?:',
                    r'as mentioned.*?:',
                    r'earlier.*?:',
                ]
                for pattern in verbose_prefixes:
                    response = re.sub(pattern, '', response, flags=re.IGNORECASE | re.DOTALL)
                
                # Remove any references to previous conversations
                response = re.sub(r'previous.*?conversation.*?:', '', response, flags=re.IGNORECASE)
                response = re.sub(r'as.*?discussed.*?:', '', response, flags=re.IGNORECASE)
                response = re.sub(r'earlier.*?:', '', response, flags=re.IGNORECASE)
                
                # Remove script-like content (the user mentioned seeing script format)
                response = re.sub(r'\[CUT TO:.*?\]', '', response, flags=re.IGNORECASE | re.DOTALL)
                response = re.sub(r'NARRATOR.*?:', '', response, flags=re.IGNORECASE | re.DOTALL)
                response = re.sub(r'INT\.|EXT\.', '', response, flags=re.IGNORECASE)
                
                # If still too long, try to extract the core answer
                if len(response) > 300:
                    # Look for the actual content after common markers
                    for marker in ['\n\n', '. ', ':', 'answer is', ':', '?']:
                        parts = response.split(marker, 1)
                        if len(parts) > 1 and len(parts[1].strip()) > 30:
                            response = parts[1].strip()
                            break
                
                # Final cleanup - remove extra whitespace
                response = re.sub(r'\s+', ' ', response).strip()
                
                logger.info(f"Successfully got response from {model} via CLI (cleaned: {len(response)} chars)")
                return response
        except subprocess.TimeoutExpired:
            logger.warning(f"Model {model} timed out")
            last_error = f"Model {model} timed out after 120 seconds"
            continue
        except subprocess.CalledProcessError as e:
            stderr_text = e.stderr.decode('utf-8', errors='ignore') if e.stderr else ""
            stdout_text = e.stdout.decode('utf-8', errors='ignore') if e.stdout else ""
            
            # Extract meaningful error message
            error_msg = stderr_text or stdout_text or str(e)
            # Filter ANSI codes
            error_msg = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', error_msg)
            error_msg = error_msg.strip()
            
            logger.warning(f"Model {model} failed: {error_msg}")
            last_error = error_msg
            
            # If it's a memory error, try next model
            if "memory" in error_msg.lower() or "system memory" in error_msg.lower():
                logger.info(f"Memory error with {model}, trying next model...")
                continue
            # For other errors, also try next model
            continue
        except Exception as e:
            logger.warning(f"Model {model} error: {e}")
            last_error = str(e)
            continue
    
    # If all models failed, raise an error with helpful message
    error_message = f"All LLM models failed. Last error: {last_error}"
    if "memory" in str(last_error).lower():
        error_message += "\n\nTip: Your system doesn't have enough memory for the available models. Consider:\n"
        error_message += "1. Installing a smaller model: ollama pull tinyllama\n"
        error_message += "2. Freeing up system memory\n"
        error_message += "3. Using a system with more RAM"
    
    raise RuntimeError(error_message)


