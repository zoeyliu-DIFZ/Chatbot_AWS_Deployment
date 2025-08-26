import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from langgraph_workflow_optimized import graph
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Tuple, Any
import uuid

class ChatAgent:
    """Chat agent using LangGraph workflow"""
    
    def __init__(self):
        self.graph = graph
    
    def query(self, user_input: str, chat_history: List[Tuple[str, str]] = None) -> str:
        """Query the agent with user input using LangGraph workflow"""
        try:
            print(f"🔍 Processing query: {user_input}")
            
            # Convert chat history to LangChain message format
            messages = []
            if chat_history:
                for role, content in chat_history:
                    if role == "human":
                        messages.append(HumanMessage(content=content))
                    # Note: We'll only include human messages for now to keep it simple
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            # Initialize state
            state = {
                "messages": messages,
                "next": None,
                "message_type": None,
                "short_mem": {"user_queries": [], "system_resps": []},
                "organize": {
                    "conditions": [],
                    "filters": [],
                    "query_type": None
                }
            }
            
            print(f"🚀 Starting LangGraph workflow...")
            print(f"📊 Initial state: {state}")
            
            # Generate unique thread and checkpoint IDs
            thread_id = str(uuid.uuid4())
            checkpoint_id = str(uuid.uuid4())
            
            # Run the graph with required configuration
            result = self.graph.invoke(
                state,
                config={
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id
                }
            )
            
            print(f"✅ LangGraph workflow completed")
            print(f"📊 Final result: {result}")
            
            # Extract the response from the final message
            if result.get("messages") and len(result["messages"]) > 0:
                # Get the last assistant message
                for message in reversed(result["messages"]):
                    if hasattr(message, 'content') and message.content and isinstance(message, AIMessage):
                        print(f"💬 Response extracted: {message.content[:100]}...")
                        return message.content
            
            print("⚠️ No valid response found in result")
            return "I'm sorry, I couldn't generate a response. Please try again."
            
        except Exception as e:
            print(f"❌ Error in ChatAgent.query: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error processing request: {str(e)}"
    
    def query_with_path(self, user_input: str, chat_history: List[Tuple[str, str]] = None) -> Tuple[str, dict]:
        """Query the agent and return both response and workflow path information"""
        try:
            print(f"🔍 Processing query with path tracking: {user_input}")
            
            # Convert chat history to LangChain message format
            messages = []
            if chat_history:
                for role, content in chat_history:
                    if role == "human":
                        messages.append(HumanMessage(content=content))
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            # Initialize state
            state = {
                "messages": messages,
                "next": None,
                "message_type": None,
                "short_mem": {"user_queries": [], "system_resps": []},
                "organize": {
                    "conditions": [],
                    "filters": [],
                    "query_type": None
                }
            }
            
            print(f"🚀 Starting LangGraph workflow with path tracking...")
            
            # Generate unique thread and checkpoint IDs
            thread_id = str(uuid.uuid4())
            checkpoint_id = str(uuid.uuid4())
            
            # Track the workflow path
            workflow_path = []
            current_state = state.copy()
            
            # Run the graph with path tracking
            result = self.graph.invoke(
                state,
                config={
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id
                }
            )
            
            print(f"✅ LangGraph workflow completed")
            
            # Extract the response from the final message
            response = "I'm sorry, I couldn't generate a response. Please try again."
            if result.get("messages") and len(result["messages"]) > 0:
                for message in reversed(result["messages"]):
                    if hasattr(message, 'content') and message.content and isinstance(message, AIMessage):
                        response = message.content
                        break
            
            # Extract workflow information
            workflow_info = {
                "path": workflow_path,
                "intent_type": result.get("message_type"),
                "final_agent": result.get("next"),
                "final_state": result
            }
            
            return response, workflow_info
            
        except Exception as e:
            print(f"❌ Error in ChatAgent.query_with_path: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error processing request: {str(e)}", {"path": [], "intent_type": "ERROR", "final_agent": None}