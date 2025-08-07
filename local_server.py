from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple, Optional
import json
import os
import sys

# Add src directory to path
sys.path.append('src')

from agent import ChatAgent

app = FastAPI(title="AI Chat Assistant - Local Dev", version="1.0.0")

# Add CORS middleware, allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be more strict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[Tuple[str, str]]] = []

# Response model
class ChatResponse(BaseModel):
    response: str

# Initialize agent
try:
    agent = ChatAgent()
    print("✅ Agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing agent: {e}")
    agent = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Chat Assistant Local Server is running!", "status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - simulate Lambda function functionality"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        # Call agent to process request
        response = agent.query(request.message, request.chat_history)
        
        return ChatResponse(response=response)
        
    except Exception as e:
        print(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "agent_status": "initialized" if agent else "error",
        "environment": "local_development"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Chat Assistant Local Server...")
    print("📍 API will be available at: http://localhost:5000")
    print("📖 API documentation at: http://localhost:5000/docs")
    print("🔗 Frontend should connect to: http://localhost:5000/chat")
    
    uvicorn.run("local_server:app", host="0.0.0.0", port=5000, reload=True) 