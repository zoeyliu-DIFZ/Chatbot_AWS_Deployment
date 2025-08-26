from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import extract_prompt_content

def new_query_agent(state, llm, store):
    system_prompt = extract_prompt_content("src/nodes/prompts/NewQueryAgent-RequestOrganization.md")
    last_message = state["messages"][-1]
    
    # Get the organize state from condition_organizer
    organize_state = state.get("organize", {})
    
    # Prepare context with organized conditions
    conditions_context = ""
    if organize_state.get("conditions") or organize_state.get("filters"):
        conditions_context = f"\n\nOrganized Search Conditions from previous step:\n{str(organize_state)}"

    messages = [
        SystemMessage(content=system_prompt + conditions_context),
        HumanMessage(content=last_message.content)
    ]
    reply = llm.invoke(messages)

    # Write to long-term memory including organize state
    if store:
        store.put(("query", "history"), datetime.utcnow().isoformat(), {
            "query": last_message.content,
            "response": reply.content,
            "organize_state": organize_state
        })

    return {
        "messages": [AIMessage(content=reply.content)],
        "organize": organize_state,  # Preserve the organize state
        "short_mem": {}
    } 