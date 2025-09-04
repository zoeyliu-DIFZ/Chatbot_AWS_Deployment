from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import extract_prompt_content

def intent_recognizer(state, llm, store):
    """intent recognizer"""
    system_prompt = extract_prompt_content("src/nodes/prompts/IntentRecognizer.md")
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)

    # Record user input in long-term memory
    if store:
        store.put(("user", "queries"), datetime.utcnow().isoformat(), last_message.content)

    # AI-based intent recognition
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=last_message.content)
    ]
    result = classifier_llm.invoke(messages)
    
    # Direct routing based on intent (no separate router needed)
    next_agent = "other_agent"  # default
    if result.message_type == "GENERAL":
        next_agent = "general_agent"
    elif result.message_type == "NEW_QUERY":
        next_agent = "condition_organizer"
    elif result.message_type == "ADJUST_FILTER":
        next_agent = "condition_organizer"

    # Record both classification and routing in one step
    if store:
        store.put(("system", "actions"), datetime.utcnow().isoformat(), {
            "action": "intent_classification_and_routing",
            "message_type": result.message_type,
            "routed_to": next_agent
        })

    # Return state with routing decision
    return {
        "message_type": result.message_type,
        "next": next_agent,
        "messages": state["messages"],
        "short_mem": state.get("short_mem", {})  # Preserve existing short_mem
    }

class MessageClassifier(BaseModel):
    message_type: Literal["GENERAL", "NEW_QUERY", "ADJUST_FILTER", "OTHER"] = Field(
        ..., description="Identify the intent of the user's current message for downstream processing."
    ) 