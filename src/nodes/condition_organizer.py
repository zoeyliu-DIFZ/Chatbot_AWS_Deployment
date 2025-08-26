from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import extract_prompt_content

def condition_organizer(state, llm, store):
    system_prompt = extract_prompt_content("src/nodes/prompts/ConditionOrganizer.md")
    last_message = state["messages"][-1]
    
    # Get current organize state or create a new one
    current_organize_state = state.get("organize", {
        "conditions": [],
        "filters": [],
        "query_type": None
    })

    # Prepare the prompt with current state context if it exists
    context_message = ""
    if current_organize_state.get("conditions") or current_organize_state.get("filters"):
        context_message = f"\n\nCurrent conditions list: {json.dumps(current_organize_state, indent=2)}"

    messages = [
        SystemMessage(content=system_prompt + context_message),
        HumanMessage(content=last_message.content)
    ]
    reply = llm.invoke(messages)

    # Parse the JSON response and update organize state
    updated_organize_state = current_organize_state
    try:
        # Extract JSON from the response
        json_content = reply.content.strip()
        if json_content.startswith('```json'):
            json_content = json_content[7:-3].strip()
        elif json_content.startswith('```'):
            json_content = json_content[3:-3].strip()
        
        parsed_response = json.loads(json_content)
        
        # Update the organize state with the parsed response
        updated_organize_state.update(parsed_response)
        
    except (json.JSONDecodeError, Exception) as e:
        # If parsing fails, log the error but continue with the current state
        if store:
            store.put(("condition", "errors"), datetime.utcnow().isoformat(), {
                "error": str(e),
                "response": reply.content,
                "request": last_message.content
            })

    # Write to long-term memory
    if store:
        store.put(("condition", "history"), datetime.utcnow().isoformat(), {
            "request": last_message.content,
            "response": reply.content,
            "parsed_state": updated_organize_state
        })

    return {
        "messages": [AIMessage(content=reply.content)],
        "message_type": state.get("message_type"),  # Preserve the original message type
        "organize": updated_organize_state,  # Update the organize state
        "short_mem": {}
    }
    

