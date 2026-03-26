from abc import ABC, abstractmethod
from typing import List, Any
from agent.models import AgentResponse, InternalMessage

class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self, 
        messages: List[InternalMessage], 
        tools: List[dict] = None
    ) -> AgentResponse:
        """Sends messages to the LLM and returns a standardized Response."""
        pass

    @abstractmethod
    def format_tools(self, tools: List[dict]) -> Any:
        """Converts generic tool schemas to provider-specific formats."""
        pass
