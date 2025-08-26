from datetime import datetime
from langchain_core.messages import SystemMessage, AIMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import extract_prompt_content

def general_agent(state, llm, store):
    system_prompt = extract_prompt_content("src/nodes/prompts/GENERALAgent.md")
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    reply = llm.invoke(messages)

    # Write to long-term memory
    if store:
        store.put(("user", "queries"), datetime.utcnow().isoformat(), state["messages"][-1].content)

    return {
        "messages": [AIMessage(content=reply.content)],
        "short_mem": {
            "system_resps": [reply.content]
        }
    } 
