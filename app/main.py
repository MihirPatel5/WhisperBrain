from fastapi import FastAPI, Request, HTTPException
from fastapi.websockets import WebSocket
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.ws import voice_pipeline
from app.api import voice_clone
from app.services.analytics import get_analytics
from app.services.export import get_export_service
from app.services.user_preferences import get_user_preferences
from app.middleware.rate_limiter import get_rate_limiter
import os
import time

app = FastAPI()

# CORS Configuration for Production
# Update CORS_ORIGINS environment variable with your frontend URLs
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(voice_clone.router)

# Phase 4: Model selection endpoint
@app.get("/api/models")
async def get_models_endpoint(request: Request):
    """Get available models and statistics"""
    from app.services.model_selector import get_model_selector
    
    selector = get_model_selector()
    return JSONResponse(content={
        "available_models": selector.get_available_models(),
        "current_model": selector.get_current_model(),
        "stats": selector.get_model_stats()
    })

# Phase 4: Tool execution endpoint
@app.post("/api/tools/execute")
async def execute_tool_endpoint(request: Request):
    """Execute a tool"""
    from app.services.tool_executor import get_tool_executor
    
    data = await request.json()
    tool_name = data.get('tool_name')
    parameters = data.get('parameters', {})
    
    executor = get_tool_executor()
    result = executor.execute_tool_call(tool_name, parameters)
    
    return JSONResponse(content=result)

# Phase 4: RAG knowledge base endpoint
@app.post("/api/rag/knowledge")
async def add_knowledge_endpoint(request: Request):
    """Add knowledge to RAG knowledge base"""
    from app.services.rag import get_rag_service
    
    data = await request.json()
    topic = data.get('topic')
    content = data.get('content')
    metadata = data.get('metadata')
    
    rag_service = get_rag_service()
    rag_service.add_knowledge(topic, content, metadata)
    
    return JSONResponse(content={"status": "success", "topic": topic})

@app.get("/api/rag/stats")
async def get_rag_stats_endpoint(request: Request):
    """Get RAG statistics"""
    from app.services.rag import get_rag_service
    
    rag_service = get_rag_service()
    return JSONResponse(content=rag_service.get_knowledge_stats())

# Phase 3: Analytics endpoint
@app.get("/api/analytics")
async def get_analytics_endpoint(request: Request):
    """Get analytics statistics"""
    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()
    allowed, error = rate_limiter.is_allowed(f"analytics_{client_id}")
    if not allowed:
        raise HTTPException(status_code=429, detail=error)
    
    analytics = get_analytics()
    return JSONResponse(content=analytics.get_stats())

# Phase 3: Export endpoint
@app.post("/api/export")
async def export_conversation(request: Request):
    """Export conversation"""
    # Rate limiting
    client_id = request.client.host if request.client else "unknown"
    rate_limiter = get_rate_limiter()
    allowed, error = rate_limiter.is_allowed(f"export_{client_id}")
    if not allowed:
        raise HTTPException(status_code=429, detail=error)
    
    data = await request.json()
    session_id = data.get('session_id')
    conversation_history = data.get('conversation_history', [])
    format = data.get('format', 'json')
    
    export_service = get_export_service()
    result = export_service.export_conversation(session_id, conversation_history, format)
    
    return JSONResponse(content=result)

# Phase 3: Download export
@app.get("/api/export/{export_id}")
async def download_export(export_id: str):
    """Download exported conversation"""
    export_service = get_export_service()
    export_info = export_service.get_export(export_id)
    
    if not export_info:
        raise HTTPException(status_code=404, detail="Export not found")
    
    from pathlib import Path
    export_path = Path(export_info['path'])
    if not export_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
    
    return FileResponse(
        path=export_path,
        filename=export_info['filename'],
        media_type=export_info.get('mime_type', 'application/octet-stream')
    )

# Phase 5: User Preferences endpoints
@app.get("/api/preferences")
async def get_preferences_endpoint(request: Request):
    """Get user preferences"""
    preferences = get_user_preferences()
    return JSONResponse(content=preferences.get_all_preferences())

@app.post("/api/preferences")
async def update_preferences_endpoint(request: Request):
    """Update user preferences"""
    data = await request.json()
    preferences = get_user_preferences()
    preferences.update_preferences(data)
    return JSONResponse(content={"status": "success", "preferences": preferences.get_all_preferences()})

@app.get("/api/preferences/{category}/{key}")
async def get_preference_endpoint(category: str, key: str):
    """Get a specific preference"""
    preferences = get_user_preferences()
    value = preferences.get_preference(category, key)
    return JSONResponse(content={"category": category, "key": key, "value": value})

@app.post("/api/preferences/reset")
async def reset_preferences_endpoint():
    """Reset preferences to defaults"""
    preferences = get_user_preferences()
    preferences.reset_to_defaults()
    return JSONResponse(content={"status": "success", "preferences": preferences.get_all_preferences()})

@app.websocket("/voice")
async def websocket_endpoint(websocket: WebSocket):
    await voice_pipeline(websocket)