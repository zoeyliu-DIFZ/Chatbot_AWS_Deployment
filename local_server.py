from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple, Optional, Dict, Any
import json
import os
import sys

# Add src directory to path
sys.path.append('src')

from agent import ChatAgent
from dynamodb_manager import db_manager

app = FastAPI(title="AI Chat Assistant - Local Dev", version="1.0.0")

# Add CORS middleware, allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be more strict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    message_count: int
    metadata: Dict[str, Any]

class ChatHistoryResponse(BaseModel):
    session_id: str
    timestamp: str
    message_id: str
    role: str
    content: str
    metadata: Dict[str, Any]

# Response model - updated to include workflow path
class ChatResponse(BaseModel):
    response: str
    session_id: str
    workflow_path: Optional[List[str]] = None
    intent_type: Optional[str] = None
    final_agent: Optional[str] = None

# Initialize agent with LangGraph workflow
try:
    print("🚀 Initializing LangGraph Agent...")
    agent = ChatAgent()
    print("✅ LangGraph Agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing LangGraph agent: {e}")
    import traceback
    traceback.print_exc()
    agent = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Chat Assistant Local Server is running!", "status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - simulate Lambda function functionality with DynamoDB integration"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        print(f"📨 Received chat request: {request.message}")
        
        # Get or create session ID
        session_id = request.session_id
        if not session_id:
            # Create new session
            session_id = db_manager.create_session(metadata={
                'user_agent': 'local_development',
                'source_ip': '127.0.0.1'
            })
            print(f"🆕 Created new session: {session_id}")
        else:
            print(f"🔄 Using existing session: {session_id}")
        
        # Get chat history from DynamoDB
        chat_history_messages = db_manager.get_chat_history(session_id, limit=20)
        print(f"📚 Loaded {len(chat_history_messages)} messages from session {session_id}")
        
        # Debug: Print recent messages
        for i, msg in enumerate(chat_history_messages[-5:]):  # Show last 5 messages
            print(f"   Message {i+1}: {msg['role']} - {msg['content'][:50]}...")
        
        # Convert to format expected by agent
        chat_history = []
        for msg in chat_history_messages:
            if msg['role'] == 'user':
                chat_history.append(('human', msg['content']))
            elif msg['role'] == 'assistant':
                chat_history.append(('assistant', msg['content']))
        
        print(f"🔄 Converted {len(chat_history)} messages for agent")
        
        # Call agent to process request
        print("🔄 Calling ChatAgent.query...")
        response, workflow_info = agent.query_with_path(request.message, chat_history, session_id)
        print(f"✅ ChatAgent response: {response[:100]}...")
        
        # Save user message to DynamoDB
        db_manager.add_chat_message(
            session_id=session_id,
            role='user',
            content=request.message,
            metadata={
                'workflow_path': workflow_info.get('path', []),
                'intent_type': workflow_info.get('intent_type'),
                'final_agent': workflow_info.get('final_agent')
            }
        )
        
        # Save assistant response to DynamoDB
        db_manager.add_chat_message(
            session_id=session_id,
            role='assistant',
            content=response,
            metadata={
                'workflow_path': workflow_info.get('path', []),
                'intent_type': workflow_info.get('intent_type'),
                'final_agent': workflow_info.get('final_agent')
            }
        )
        
        # Update session with latest activity
        db_manager.update_session(session_id, last_message_at=workflow_info.get('timestamp'))
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            workflow_path=workflow_info.get("path", []),
            intent_type=workflow_info.get("intent_type"),
            final_agent=workflow_info.get("final_agent")
        )
        
    except Exception as e:
        print(f"❌ Error processing chat request: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/sessions")
async def list_sessions(limit: int = 20):
    """List all sessions"""
    try:
        sessions = db_manager.list_sessions(limit=limit)
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        print(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str, limit: int = 50):
    """Get session details and history"""
    try:
        # Get session details
        session = db_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get chat history
        chat_history = db_manager.get_chat_history(session_id, limit=limit)
        
        return {
            "session": session,
            "chat_history": chat_history,
            "message_count": len(chat_history)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete session and all messages"""
    try:
        # Check if session exists
        session = db_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete session and all messages
        db_manager.delete_session(session_id)
        
        return {
            "message": "Session deleted successfully",
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check"""
    db_status = db_manager.get_status()
    return {
        "status": "healthy",
        "agent_status": "initialized" if agent else "error",
        "environment": "local_development",
        "dynamodb_status": db_status
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Chat Assistant Local Server with LangGraph and DynamoDB...")
    print("📍 API will be available at: http://localhost:5000")
    print("📖 API documentation at: http://localhost:5000/docs")
    print("🔗 Frontend should connect to: http://localhost:5000/chat")
    print("🗄️ DynamoDB tables: ai-chat-session-dev, ai-chat-history-dev")
    
    uvicorn.run("local_server:app", host="0.0.0.0", port=5000, reload=True) 