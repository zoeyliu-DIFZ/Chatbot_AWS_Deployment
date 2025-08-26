from langchain_core.prompts import ChatPromptTemplate
from backend.Agent.base_agent import BaseAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Any


class ConditionChecker(BaseAgent):
    def __init__(self, prompt_path: str):
        super().__init__(prompt_path)
        self.agent_chain = self.create_chain() 
    
    def create_chain(self):
        llm = self.llm_factory.create_claude_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_content),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}")
        ])
        return prompt | llm
    
    def query(self, user_input: str) -> Any:
        return self.agent_chain.invoke({"input": user_input})
    

