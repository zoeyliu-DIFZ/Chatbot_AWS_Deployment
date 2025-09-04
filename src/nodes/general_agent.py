from datetime import datetime
from langchain_core.messages import SystemMessage, AIMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import extract_prompt_content

def general_agent(state, llm, store):
    system_prompt = extract_prompt_content("src/nodes/prompts/GENERALAgent.md")
    
    # Get current short memory
    short_mem = state.get("short_mem", {"user_queries": [], "system_resps": []})
    
    # Create memory context
    memory_context = ""
    if short_mem.get("user_queries"):
        memory_context = f"\n\nPrevious conversation context:\nUser queries: {', '.join(short_mem['user_queries'][-3:])}\nSystem responses: {', '.join(short_mem['system_resps'][-3:])}"
    
    # Update system prompt with memory
    enhanced_prompt = system_prompt + memory_context
    
    messages = [SystemMessage(content=enhanced_prompt)] + state["messages"]
    reply = llm.invoke(messages)

    # Write to long-term memory
    if store:
        store.put(("user", "queries"), datetime.utcnow().isoformat(), state["messages"][-1].content)

    # Update short memory
    updated_short_mem = {
        "user_queries": short_mem.get("user_queries", []) + [state["messages"][-1].content],
        "system_resps": short_mem.get("system_resps", []) + [reply.content]
    }

    return {
        "messages": [AIMessage(content=reply.content)],
        "short_mem": updated_short_mem
    } 
