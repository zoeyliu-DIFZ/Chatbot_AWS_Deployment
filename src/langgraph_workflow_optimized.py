from dotenv import load_dotenv
from typing import Annotated, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_aws import ChatBedrock
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# Import local nodes
from nodes.intent_recognizer import intent_recognizer
from nodes.general_agent import general_agent
from nodes.new_query_agent import new_query_agent
from nodes.adjust_filter_agent import adjust_filter_agent
from nodes.other_agent import other_agent
from nodes.condition_organizer import condition_organizer

# Simple reducer functions
def merge_dicts(state, new_data):
    """Merge new data into state"""
    if isinstance(new_data, dict):
        for key, value in new_data.items():
            if key in state:
                if isinstance(state[key], list) and isinstance(value, list):
                    state[key].extend(value)
                elif isinstance(state[key], dict) and isinstance(value, dict):
                    state[key].update(value)
                else:
                    state[key] = value
            else:
                state[key] = value
    return state

def trim_messages(state):
    """Keep only recent messages to manage context length"""
    if "messages" in state and len(state["messages"]) > 10:
        state["messages"] = state["messages"][-10:]
    return state

load_dotenv()

# Initialize the LLM
llm = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    region_name="us-east-1",
    model_kwargs={"temperature": 0.0}
)

# Define the state type
class ShortMem(TypedDict):
    user_queries: list[str]
    system_resps: list[str]

class OrganizeState(TypedDict):
    conditions: list[str]
    filters: list[str]
    query_type: str | None

class State(TypedDict):
    messages: Annotated[list, add_messages]
    next: str | None
    message_type: str | None
    short_mem: Annotated[ShortMem, merge_dicts]
    organize: OrganizeState

# Create the optimized graph
graph_builder = StateGraph(State)

# Add nodes with debugging
def intent_recognizer_node(state, *, store=None):
    print(f"🔄 Intent Recognizer Node - Processing message: {state['messages'][-1].content[:50]}...")
    result = intent_recognizer(state, llm, store)
    print(f"✅ Intent Recognizer Result: {result}")
    return result

def general_agent_node(state, *, store=None):
    print(f"🔄 General Agent Node - Processing...")
    result = general_agent(state, llm, store)
    print(f"✅ General Agent Result: {result}")
    return result

def new_query_agent_node(state, *, store=None):
    print(f"🔄 New Query Agent Node - Processing...")
    result = new_query_agent(state, llm, store)
    print(f"✅ New Query Agent Result: {result}")
    return result

def adjust_filter_agent_node(state, *, store=None):
    print(f"🔄 Adjust Filter Agent Node - Processing...")
    result = adjust_filter_agent(state, llm, store)
    print(f"✅ Adjust Filter Agent Result: {result}")
    return result

def other_agent_node(state, *, store=None):
    print(f"🔄 Other Agent Node - Processing...")
    result = other_agent(state, llm, store)
    print(f"✅ Other Agent Result: {result}")
    return result

def condition_organizer_node(state, *, store=None):
    print(f"🔄 Condition Organizer Node - Processing...")
    result = condition_organizer(state, llm, store)
    print(f"✅ Condition Organizer Result: {result}")
    
    # Determine next step based on original message type
    message_type = result.get("message_type")
    if message_type == "NEW_QUERY":
        result["next"] = "new_query_agent"
        print(f"🔄 Routing to: new_query_agent")
    elif message_type == "ADJUST_FILTER":
        result["next"] = "adjust_filter_agent"
        print(f"🔄 Routing to: adjust_filter_agent")
    else:
        print(f"⚠️ No specific routing for message_type: {message_type}")
    
    return result

# Add nodes to graph
graph_builder.add_node("intent_recognizer", intent_recognizer_node)
graph_builder.add_node("general_agent", general_agent_node)
graph_builder.add_node("new_query_agent", new_query_agent_node)
graph_builder.add_node("adjust_filter_agent", adjust_filter_agent_node)
graph_builder.add_node("other_agent", other_agent_node)
graph_builder.add_node("condition_organizer", condition_organizer_node)

# Add edges - direct routing from smart_router!
graph_builder.add_edge(START, "intent_recognizer")

# Add conditional edges directly from smart_router to agents
graph_builder.add_conditional_edges(
    "intent_recognizer",
    lambda state: state.get("next"),
    {
        "general_agent": "general_agent",
        "condition_organizer": "condition_organizer",
        "other_agent": "other_agent"
    }
)

# Add conditional edges from condition_organizer to specific agents
graph_builder.add_conditional_edges(
    "condition_organizer",
    lambda state: state.get("next"),
    {
        "new_query_agent": "new_query_agent",
        "adjust_filter_agent": "adjust_filter_agent"
    }
)

# Add edges from agents to END
graph_builder.add_edge("general_agent", END)
graph_builder.add_edge("new_query_agent", END)
graph_builder.add_edge("adjust_filter_agent", END)
graph_builder.add_edge("other_agent", END)

# Compile the optimized graph with proper configuration
memory = MemorySaver()
lt_store = InMemoryStore()
graph = graph_builder.compile(
    checkpointer=memory, 
    store=lt_store
)

print("🚀 LangGraph workflow compiled successfully!")
print("📊 Graph structure:")
print("   START → intent_recognizer")
print("   intent_recognizer → general_agent | condition_organizer | other_agent")
print("   condition_organizer → new_query_agent | adjust_filter_agent")
print("   all agents → END") 