from abc import ABC, abstractmethod
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import os
from typing import Any

# Load environment variables
load_dotenv()

def load_and_escape_prompt(prompt_path: str) -> str:
    """Load and return prompt content from file"""
    try:
        # Try relative path first, then absolute path
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            # Try in the same directory as this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(current_dir, prompt_path)
            with open(full_path, 'r', encoding='utf-8') as file:
                return file.read()
    except FileNotFoundError:
        return "You are a helpful AI assistant."

class LLMFactory:
    """LLM factory class"""
    
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None):
        self.credentials = {
            "aws_access_key_id": aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
            "aws_secret_access_key": aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY'),
            "aws_session_token": aws_session_token or os.getenv('AWS_SESSION_TOKEN')
        }
    
    def create_claude_llm(self, temperature: float = 0, max_tokens: int = 100000) -> ChatBedrock:
        return ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name="us-east-1",
            model_kwargs={
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        )

class BaseAgent(ABC):
    """Base agent class"""
    
    def __init__(self, prompt_path: str, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None):
        self.llm_factory = LLMFactory(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )
        self.prompt_path = prompt_path
        self.prompt_content = load_and_escape_prompt(self.prompt_path)
    
    @abstractmethod
    def create_chain(self):
        """Create processing chain - subclasses must implement"""
        pass

class ChatAgent(BaseAgent):
    """Chat agent for conversational interactions"""
    
    def __init__(self, prompt_path: str = None, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None):
        # Use default prompt if none provided
        if prompt_path is None:
            prompt_path = "default_prompt.txt"
        super().__init__(prompt_path, aws_access_key_id, aws_secret_access_key, aws_session_token)
        self.agent_chain = self.create_chain() 
    
    def create_chain(self):
        llm = self.llm_factory.create_claude_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_content),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}")
        ])
        return prompt | llm
    
    def query(self, user_input: str, chat_history=None) -> str:
        """Query the agent with user input"""
        try:
            response = self.agent_chain.invoke({
                "input": user_input,
                "chat_history": chat_history or []
            })
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"Error processing request: {str(e)}"
