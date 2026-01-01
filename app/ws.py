from fastapi import WebSocket, WebSocketDisconnect
from app.stt import speech_to_text
from app.llm import chat_with_llm
from app.tts import text_to_speech
from app.services.fast_stt import speech_to_text_fast
from app.services.fast_tts import text_to_speech_fast
from app.services.vad import SimpleVAD
from app.services.memory_manager import ConversationMemory
from app.services.context_analyzer import ContextAnalyzer
from app.models.session import SessionManager
from app.services.language_detector import detect_language
from app.services.audio_buffer import StreamingAudioProcessor
from app.services.emotion_detector import EmotionDetector
from app.services.translator import Translator
from app.services.voice_cloning import VoiceCloningService
from app.services.analytics import get_analytics
from app.services.webhook import get_webhook_service
from app.services.model_selector import get_model_selector
from app.services.tool_executor import get_tool_executor
from app.services.rag import get_rag_service
from app.services.user_preferences import get_user_preferences
from app.services.error_handler import get_error_handler, ErrorType
from app.services.reconnection_manager import get_reconnection_manager
from app.middleware.rate_limiter import get_rate_limiter
from app.config.languages import DEFAULT_LANGUAGE, AUTO_DETECT_LANGUAGE
import logging
import io
import time

logger = logging.getLogger(__name__)

# Global session manager (shared across connections)
_session_manager = SessionManager(session_timeout_minutes=30)


async def voice_pipeline(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    # Phase 1.1: Session Management
    session = _session_manager.create_session()
    logger.info(f"Session created: {session.session_id} for user: {session.user_id}")
    
    # Send session info to frontend
    await websocket.send_json({
        "status": "Connected",
        "session_id": session.session_id,
        "user_id": session.user_id
    })
    
    # Initialize memory manager for intelligent conversation management
    from app.config.memory_config import MEMORY_CONFIG
    
    memory = ConversationMemory(
        max_tokens=MEMORY_CONFIG['max_tokens'],
        max_messages=MEMORY_CONFIG['max_messages'],
        summarize_threshold=MEMORY_CONFIG['summarize_threshold'],
        important_keywords=MEMORY_CONFIG['important_keywords']
    )
    
    # Initialize context analyzer to determine when context is actually needed
    context_analyzer = ContextAnalyzer()
    
    USE_CONVERSATION_HISTORY = True  # Set to False to disable context
    
    # Phase 1.2: VAD for streaming mode (optional - can be enabled via config)
    vad_enabled = False  # Set to True to enable backend VAD
    vad = SimpleVAD() if vad_enabled else None
    
    # Real-time audio processing (optimized for speed)
    USE_FAST_STT_TTS = True  # Use optimized STT/TTS (no file I/O overhead)
    audio_processor = StreamingAudioProcessor()  # In-memory audio buffering
    audio_chunks = []  # Accumulate chunks for processing
    
    # Phase 1.3: Streaming support (can be enabled)
    STREAMING_ENABLED = False  # Set to True to enable streaming responses
    
    # Phase 1.4: Language support
    current_language = DEFAULT_LANGUAGE  # Will be detected or set by user
    
    # Phase 2: Advanced Features
    # 2.2: Voice Cloning
    voice_cloning_service = VoiceCloningService()
    user_voice_id = None  # Set if user has cloned voice
    
    # 2.3: Emotion Detection
    emotion_detector = EmotionDetector()
    ENABLE_EMOTION_DETECTION = True  # Set to False to disable
    
    # 2.4: Translation
    translator = Translator()
    ENABLE_TRANSLATION = False  # Set to True to enable translation
    target_translation_language = None  # Set target language for translation
    
    # Phase 3: Enterprise Features
    # 3.1: Analytics
    analytics = get_analytics()
    ENABLE_ANALYTICS = True  # Set to False to disable
    
    # 3.2: Rate Limiting (already checked at connection)
    rate_limiter = get_rate_limiter()
    
    # 3.3: Webhooks
    webhook_service = get_webhook_service()
    ENABLE_WEBHOOKS = False  # Set to True to enable
    
    # Phase 4: AI Enhancements
    # 4.1: Multi-Model Support
    model_selector = get_model_selector()
    ENABLE_MODEL_SELECTION = True  # Set to False to disable
    
    # 4.2: Tool Use / Function Calling
    tool_executor = get_tool_executor()
    ENABLE_TOOLS = False  # Set to True to enable tool use
    
    # 4.3: RAG (Retrieval Augmented Generation)
    rag_service = get_rag_service()
    ENABLE_RAG = False  # Set to True to enable RAG
    
    # Track conversation metrics for analytics
    conversation_start_time = time.time()
    conversation_metrics = {
        'message_count': 0,
        'audio_size': 0,
        'response_times': []
    }

    try:
        while True:
            try:
                logger.info("Waiting for audio data...")
                audio_chunk = await websocket.receive_bytes()
                logger.info(f"Received audio chunk: {len(audio_chunk)} bytes")
                
                if not audio_chunk:
                    logger.warning("Received empty audio chunk")
                    continue
                
                # Real-time audio processing: accumulate chunks
                audio_chunks.append(audio_chunk)
                
                # If VAD is enabled, check for silence
                if vad_enabled and vad:
                    if vad.check(audio_chunk):
                        # Silence detected, process accumulated audio
                        logger.info("VAD detected speech end, processing accumulated audio")
                        combined_audio = b''.join(audio_chunks)
                        audio_chunks.clear()
                        vad.reset()
                    else:
                        # Continue accumulating
                        continue
                
                # For now, process when we receive chunks
                # Frontend should send a stop signal or empty chunk when done
                # Process accumulated chunks
                if len(audio_chunks) > 0:
                    combined_audio = b''.join(audio_chunks)
                else:
                    continue

                # Phase 1.4: Language Detection (if enabled)
                # Only attempt detection if we have enough audio and models are available
                if AUTO_DETECT_LANGUAGE and len(combined_audio) > 1000:
                    try:
                        detected_lang = detect_language(audio_bytes=combined_audio)
                        if detected_lang and detected_lang != current_language:
                            current_language = detected_lang
                            logger.info(f"Language detected: {current_language}")
                            await websocket.send_json({"status": f"Language: {current_language}"})
                    except Exception as e:
                        # Silently fail - use default language
                        logger.debug(f"Language detection skipped: {e}")
                        pass
                
                # Speech to text (optimized - no file I/O)
                try:
                    logger.info("Starting fast speech-to-text conversion...")
                    await websocket.send_json({"status": "Converting speech to text..."})
                    
                    if USE_FAST_STT_TTS:
                        # Use fast STT (in-memory processing)
                        text = speech_to_text_fast(combined_audio, language=current_language, use_stdin=False)
                    else:
                        # Fallback to regular STT
                        text = speech_to_text(combined_audio, language=current_language)
                    
                    logger.info(f"USER ({current_language}): {text}")
                    
                    # Clear chunks after processing
                    audio_chunks.clear()
                    
                    if not text or not text.strip():
                        logger.warning("No speech detected in audio")
                        await websocket.send_json({"status": "No speech detected", "text": ""})
                        continue
                    
                    # Send transcript back to frontend
                    await websocket.send_json({"status": "Processing with AI...", "text": text})
                except Exception as e:
                    logger.error(f"STT error: {e}", exc_info=True)
                    await websocket.send_json({"error": f"Speech recognition failed: {str(e)}"})
                    continue

                # LLM processing
                try:
                    logger.info("Processing with LLM...")
                    
                    # Determine if context is actually needed (smart context selection)
                    context = None
                    if USE_CONVERSATION_HISTORY:
                        # Get full history from memory
                        full_history = memory.get_context(max_tokens=2000)
                        
                        # Analyze if current question actually needs context
                        if context_analyzer.needs_context(text, full_history):
                            # Get only relevant context (not full history)
                            context = context_analyzer.get_relevant_context(text, full_history, max_messages=2)
                            logger.info(f"Context needed - including {len(context) if context else 0} relevant messages")
                        else:
                            # Standalone question - no context needed
                            context = None
                            logger.info("Standalone question - no context needed")
                        
                        # Add user message to memory (for future reference)
                        memory.add_message("user", text)
                        stats = memory.get_stats()
                        logger.info(f"Memory: {stats['total_messages']} msgs, {stats['total_tokens']} tokens")
                    
                    # Phase 2.3: Adjust LLM prompt based on emotion
                    emotion_context = ""
                    emotion_result = None  # Initialize
                    if ENABLE_EMOTION_DETECTION:
                        try:
                            emotion_result = emotion_detector.detect_emotion(text=text, audio_bytes=combined_audio)
                            logger.info(f"Emotion detected: {emotion_result.get('primary', {}).get('emotion', 'unknown')}")
                            await websocket.send_json({
                                "status": "Emotion detected",
                                "emotion": emotion_result.get('primary', {}).get('emotion', 'neutral'),
                                "sentiment": emotion_result.get('primary', {}).get('sentiment', 'neutral')
                            })
                        except Exception as e:
                            logger.warning(f"Emotion detection failed: {e}")
                    
                    if ENABLE_EMOTION_DETECTION and emotion_result:
                        primary = emotion_result.get('primary', {})
                        emotion = primary.get('emotion', 'neutral')
                        sentiment = primary.get('sentiment', 'neutral')
                        suggestions = primary.get('suggestions', {})
                        
                        if emotion != 'neutral' or sentiment != 'neutral':
                            emotion_context = f"\n\nUser's emotional state: {emotion} ({sentiment}). "
                            emotion_context += f"Respond with a {suggestions.get('tone', 'neutral')} tone and {suggestions.get('style', 'professional')} style."
                            if suggestions.get('empathy', False):
                                emotion_context += " Show empathy and understanding."
                    
                    # Phase 4.2: Check for tool use
                    tool_result = None
                    if ENABLE_TOOLS:
                        tool_result = tool_executor.auto_detect_and_execute(text)
                        if tool_result and tool_result.get('success'):
                            # Include tool result in prompt
                            tool_info = f"\n\nTool result ({tool_result.get('tool', 'unknown')}): {tool_result}"
                            text = text + tool_info
                            logger.info(f"Tool executed: {tool_result.get('tool')}")
                    
                    # Phase 4.3: Retrieve RAG context
                    rag_context = []
                    if ENABLE_RAG:
                        rag_context = rag_service.retrieve_context(text, max_results=3)
                        if rag_context:
                            logger.info(f"Retrieved {len(rag_context)} RAG contexts")
                    
                    # Phase 4.1: Select model based on use case
                    selected_model = None
                    if ENABLE_MODEL_SELECTION:
                        selected_model = model_selector.select_model(text=text)
                        logger.info(f"Selected model: {selected_model}")
                    
                    # Phase 3.1: Track performance - LLM start
                    llm_start_time = time.time()
                    
                    # Phase 1.3: Streaming or regular LLM response
                    reply = ""
                    if STREAMING_ENABLED:
                        # Stream response word-by-word
                        from app.services.streaming_llm import stream_llm_response
                        logger.info("Streaming LLM response...")
                        await websocket.send_json({"status": "Streaming response...", "streaming": True})
                        
                        # Add emotion context to text if available
                        text_for_llm = text + emotion_context if emotion_context else text
                        async for chunk in stream_llm_response(text_for_llm, context):
                            reply += chunk
                            # Send each chunk to frontend
                            await websocket.send_json({
                                "status": "streaming",
                                "chunk": chunk,
                                "partial_response": reply
                            })
                        
                        await websocket.send_json({"status": "Streaming complete", "streaming": False})
                    else:
                        # Regular (non-streaming) response
                        # Add emotion context to prompt if available
                        text_with_emotion = text + emotion_context if emotion_context else text
                        # Phase 4: Enhanced LLM call with model selection and RAG
                        reply = chat_with_llm(
                            text_with_emotion,
                            context,
                            model_preference=selected_model,
                            use_case=None,  # Auto-detected from text
                            rag_context=rag_context if rag_context else None
                        )
                    
                    # Phase 3.1: Track LLM performance
                    llm_duration = time.time() - llm_start_time
                    if analytics:
                        analytics.track_performance('llm', llm_duration, session.session_id)
                        conversation_metrics['response_times'].append(llm_duration)
                    
                    logger.info(f"BOT: {reply}")
                    
                    # Update session activity
                    session.increment_conversation()
                    conversation_metrics['message_count'] += 1
                    
                    # Phase 3.3: Send webhook for message
                    if webhook_service.enabled:
                        await webhook_service.send_webhook('message', {
                            'session_id': session.session_id,
                            'user_id': session.user_id,
                            'user_message': text,
                            'assistant_message': reply,
                            'timestamp': time.time()
                        })
                    
                    # Store assistant response in memory
                    if USE_CONVERSATION_HISTORY:
                        memory.add_message("assistant", reply)
                        logger.info(f"Updated memory: {memory.get_stats()}")
                except Exception as e:
                    logger.error(f"LLM error: {e}", exc_info=True)
                    await websocket.send_json({"error": f"LLM processing failed: {str(e)}"})
                    continue

                # Send response text before audio
                await websocket.send_json({"status": "Generating speech...", "response": reply})
                
                # Text to speech with language support (optimized - no file I/O)
                try:
                    logger.info("Generating speech (fast mode)...")
                    
                    if USE_FAST_STT_TTS:
                        # Use fast TTS (in-memory processing)
                        audio_reply = text_to_speech_fast(reply, language=current_language, use_stdout=False)
                    else:
                        # Fallback to regular TTS
                        audio_reply = text_to_speech(reply, language=current_language)
                    
                    logger.info(f"Sending audio response: {len(audio_reply)} bytes")
                    await websocket.send_bytes(audio_reply)
                    logger.info("Audio response sent successfully")
                except Exception as e:
                    logger.error(f"TTS error: {e}", exc_info=True)
                    await websocket.send_json({"error": f"Text-to-speech failed: {str(e)}"})
                    continue

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                # Cleanup session
                _session_manager.remove_session(session.session_id)
                break
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                try:
                    await websocket.send_json({"error": str(e)})
                except:
                    pass
                break

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
        # Cleanup session
        if 'session' in locals():
            _session_manager.remove_session(session.session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        # Cleanup session on error
        if 'session' in locals():
            _session_manager.remove_session(session.session_id)