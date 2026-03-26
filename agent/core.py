import json
from typing import List
from config import MAX_MESSAGES
from tools.registry import tools as static_tools, AVAILABLE_TOOLS
from agent.logger import log_step
from agent.models import InternalMessage, AgentResponse
from agent.providers.base import LLMProvider


SYSTEM_MESSAGE = InternalMessage(
    role="system",
    content=(
        "You are a versatile research assistant with access to real-time tools.\n\n"
        "Available tools:\n"
        "1. EXA SEARCH - Use this for web-based queries. Always cite source URLs.\n"
        "2. WEATHER DATA - Use this to retrieve current weather conditions using coordinates.\n\n"
        "Instructions:\n"
        "- Choose the most appropriate tool for the task.\n"
        "- You may use multiple tools in sequence if necessary."
    )
)


async def run_agent(
    user_query: str,
    conversation: List[InternalMessage],
    provider: LLMProvider,
    mcp_client=None,
):
    all_tools = list(static_tools)

    if mcp_client:
        raw_mcp = await mcp_client.session.list_tools()
        mcp_tool_definitions = mcp_client.to_generic_tool_defs(raw_mcp.tools)
        all_tools.extend(mcp_tool_definitions)

    while len(conversation) > MAX_MESSAGES:
        if len(conversation) > 1:
            conversation.pop(1)

    iteration_count = 0

    while True:
        iteration_count += 1
        response: AgentResponse = await provider.generate(conversation, tools=all_tools)

        conversation.append(
            InternalMessage(
                role="assistant",
                content=response.text or "",
                tool_calls=response.tool_calls,
            )
        )

        log_step(iteration_count, response.tool_calls)

        if not response.tool_calls:
            print(f"\n{'*' * 10} AGENT FINISHED {'*' * 10}")
            print(response.text)
            break

        for tool_call in response.tool_calls:
            f_name = tool_call.name
            f_args = tool_call.arguments

            if f_name in AVAILABLE_TOOLS:
                result = AVAILABLE_TOOLS[f_name](**f_args)
            else:
                print(f"  [MCP] Routing to Local Server: {f_name}")
                result = await mcp_client.call_tool(f_name, f_args)

            conversation.append(
                InternalMessage(
                    role="tool",
                    content=json.dumps(result),
                    tool_call_id=tool_call.id,
                )
            )

    return response
