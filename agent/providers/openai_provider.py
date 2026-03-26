import json
from typing import List
from config import client  # Using your existing SDK client
from agent.providers.base import LLMProvider
from agent.models import AgentResponse, ToolCall, InternalMessage

class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    def format_tools(self, tools: List[dict]):
        # OpenAI SDK expects the list of tool definitions as-is
        return tools

    async def generate(self, messages: List[InternalMessage], tools=None) -> AgentResponse:
        api_input = []
        
        for m in messages:
            if m.role == "tool":
                # Correct mapping for the new SDK's tool results
                api_input.append({
                    "type": "function_call_output",
                    "call_id": m.tool_call_id,
                    "output": m.content
                })
            elif m.role == "assistant" and m.tool_calls:
                # If the assistant had tool calls in the history, 
                # we must put them back in the SDK's format
                if m.content:
                    api_input.append({"role": "assistant", "content": m.content})
                
                for tc in m.tool_calls:
                    api_input.append({
                        "type": "function_call",
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                        "call_id": tc.id
                    })
            else:
                # Standard User/System/Assistant text messages
                api_input.append({"role": m.role, "content": m.content})
        
        # Call the SDK
        response = client.responses.create(
            model=self.model,
            tools=self.format_tools(tools) if tools else None,
            input=api_input,
        )

        # Convert SDK output back to our Agnostic objects
        standard_tool_calls = []
        for item in response.output:
            if hasattr(item, 'type') and item.type == "function_call":
                standard_tool_calls.append(ToolCall(
                    id=item.call_id,
                    name=item.name,
                    arguments=json.loads(item.arguments)
                ))

        return AgentResponse(
            text=response.output_text, 
            tool_calls=standard_tool_calls
        )