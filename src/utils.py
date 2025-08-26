import random
import string
import json
import re
from typing import Dict, Any
from dotenv import load_dotenv
import os

load_dotenv()

### Helper Functions - Generate Session Key
def generate_session_key():
    """Generate a random session key."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


### Helper Functions - Extract JSON from Response
def extract_JSON_from_response(response: str) -> Dict[str, Any]:
    """
    Extract conditions from the LLM JSON response
    
    Args:
        response: The raw string response from the LLM
        
    Returns:
        A dictionary of extracted conditions
    """
    try:
        # Try to parse the entire response as JSON
        conditions = json.loads(response)
        return conditions
    except json.JSONDecodeError:
        # If that fails, try to extract JSON from within the response text
        try:
            # Look for JSON-like structure between curly braces
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                conditions = json.loads(json_str)
                return conditions
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # If JSON extraction fails completely, return empty dict
        print("Warning: Could not parse JSON from response")
        return {} 
    

def extract_JSON_from_response_Langchain(response: str):
    """
    Try to extract and parse JSON from the LLM response.
    1. Find ```json ... ``` code block; if not found, then find {...}
    2. Replace \n with \\n
    """
    # remove ```json ... ```
    code_block = re.search(r"```json(.*?)```", response, flags=re.DOTALL | re.IGNORECASE)
    if code_block:
        candidate = code_block.group(1).strip()
    else:
        # Backtrack: Find the outermost {...}
        brace_match = re.search(r"\{.*\}", response, flags=re.DOTALL)
        if not brace_match:
            print("Warning: No JSON object found in response")
            return {}
        candidate = brace_match.group(0)

    # Replace \n with \\n
    def _escape_newlines(match: re.Match):
        return match.group(0).replace("\n", "\\n")

    candidate = re.sub(
        r'"(?:[^"\\]|\\.)*"',     # non-greedy match a valid JSON string
        _escape_newlines,
        candidate,
        flags=re.DOTALL
    )

    # Parse the JSON
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        print("Warning: Still failed to parse JSON ->", e)
        return {}
    

def load_and_escape_prompt(prompt_path: str) -> str:
    """Load and escape prompt content"""
    prompt_content = extract_prompt_content(prompt_path)
    return prompt_content.replace("{", "{{").replace("}", "}}")


def extract_prompt_content(file_path):
    """Extract prompt content from markdown files, handling both local and Lambda environments"""
    
    # Try multiple possible paths
    possible_paths = []
    
    # If the path already has 'src/' prefix, try it as-is
    if file_path.startswith('src/'):
        possible_paths.append(file_path)
        # Also try without the 'src/' prefix
        possible_paths.append(file_path[4:])
    else:
        # If no 'src/' prefix, try with it
        possible_paths.append(f"src/{file_path}")
        # And try as-is
        possible_paths.append(file_path)
    
    # Try each possible path
    for path in possible_paths:
        try:
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            start_line = None
            for i, line in enumerate(lines):
                if "########## Prompt Content ##########" in line:
                    start_line = i + 1
                    break
            
            if start_line is not None:
                prompt_lines = lines[start_line:]
                return ''.join(prompt_lines).strip()
            else:
                return "No prompt found"
                
        except FileNotFoundError:
            continue
    
    # If all paths fail, return error message
    print(f"Warning: Could not find prompt file. Tried paths: {possible_paths}")
    return "Prompt file not found"


def extract_response(result):
    """Extract response content"""
    if hasattr(result, 'content'):  # AIMessage
        return result.content
    elif isinstance(result, dict):
        if 'output' in result:
            if isinstance(result['output'], list):
                return result['output'][0]['text']  # complex format
            else:
                return result['output']  # AgentExecutor format
    return str(result)