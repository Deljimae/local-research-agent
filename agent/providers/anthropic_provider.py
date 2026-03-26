from typing import List
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY
from agent.providers.base import LLMProvider
from agent.models import AgentResponse, ToolCall, InternalMessage


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = "claude-3-5-sonnet-latest"):
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for AnthropicProvider")
        self.model = model
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

    def format_tools(self, tools: List[dict]):
        formatted = []
        for t in tools:
            formatted.append(
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
                }
            )
        return formatted

    def _format_messages(self, messages: List[InternalMessage]):
        system_parts = []
        api_messages = []

        for m in messages:
            if m.role == "system":
                if m.content:
                    system_parts.append(m.content)
                continue

            if m.role == "user":
                api_messages.append({"role": "user", "content": m.content})
                continue

            if m.role == "assistant":
                blocks = []
                if m.content:
                    blocks.append({"type": "text", "text": m.content})
                for tc in m.tool_calls:
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.arguments,
                        }
                    )
                if blocks:
                    api_messages.append({"role": "assistant", "content": blocks})
                continue

            if m.role == "tool":
                api_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": m.tool_call_id,
                                "content": m.content,
                            }
                        ],
                    }
                )

        system_text = "\n\n".join(system_parts) if system_parts else None
        return system_text, api_messages

    async def generate(self, messages: List[InternalMessage], tools=None) -> AgentResponse:
        system_text, api_messages = self._format_messages(messages)

        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": api_messages,
        }
        if system_text:
            kwargs["system"] = system_text
        if tools:
            kwargs["tools"] = self.format_tools(tools)

        response = self.client.messages.create(**kwargs)

        text_chunks = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_chunks.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    )
                )

        text = "\n".join([t for t in text_chunks if t]).strip() or None
        return AgentResponse(text=text, tool_calls=tool_calls)
