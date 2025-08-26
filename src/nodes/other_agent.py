from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import extract_prompt_content

def other_agent(state, llm, store):
    system_prompt = extract_prompt_content("src/nodes/prompts/OtherAgent.md")
    last_message = state["messages"][-1]

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=last_message.content)
    ]
    reply = llm.invoke(messages)

    # Write to long-term memory
    if store:
        store.put(("misc", "history"), datetime.utcnow().isoformat(), {
            "request": last_message.content,
            "response": reply.content
        })

    return {
        "messages": [AIMessage(content=reply.content)],
        "short_mem": {}
    } 