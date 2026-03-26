import asyncio
from config import LLM_PROVIDER, LLM_MODEL
from agent.core import run_agent, SYSTEM_MESSAGE
from agent.memory import load_long_term_memory, save_memory_notes
from agent.reflection import reflect_on_session
from agent.mcp_client import LocalMCPClient
from agent.models import InternalMessage
from agent.skill_selector import select_skill_for_turn
from agent.skills import build_available_skills_context, discover_skills, load_skill_context
from agent.providers.openai_provider import OpenAIProvider


def build_provider():
    if LLM_PROVIDER == "anthropic":
        from agent.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(model=LLM_MODEL or "claude-3-5-sonnet-latest")
    if LLM_PROVIDER == "openai":
        return OpenAIProvider(model=LLM_MODEL or "gpt-4o-mini")
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


async def main():
    print("--- AI Agent (Model Agnostic) + Local-Intel MCP Active ---")

    llm = build_provider()
    print(f"Provider: {LLM_PROVIDER}")
    print(f"Model: {llm.model}")

    skills_registry = discover_skills()
    if skills_registry:
        print("Skills:")
        for skill in skills_registry.values():
            print(f"- {skill.name}: {skill.description}")
    else:
        print("Skills: none discovered")

    mcp_bridge = LocalMCPClient()
    await mcp_bridge.connect()

    session_history = [SYSTEM_MESSAGE]

    try:
        while True:
            user_query = input("\nQuery (or 'exit'): ")
            if user_query.lower() in ["exit", "quit"]:
                print("Reflecting... 🧠")
                reflections = reflect_on_session(session_history)
                save_memory_notes(reflections)
                break

            if not user_query.strip():
                continue

            session_history.append(InternalMessage(role="user", content=user_query))

            relevant_memories = load_long_term_memory(user_query)
            memory_context = InternalMessage(
                role="system",
                content=f"PREVIOUS KNOWLEDGE:\n{relevant_memories}",
            )

            turn_context = [memory_context]

            if skills_registry:
                turn_context.append(
                    InternalMessage(
                        role="system",
                        content=build_available_skills_context(skills_registry),
                    )
                )

                selected_skill, selection_reason = await select_skill_for_turn(
                    user_query,
                    skills_registry,
                    llm,
                )
                if selected_skill:
                    print(f"Selected skill: {selected_skill.name} ({selection_reason})")
                    turn_context.append(
                        InternalMessage(
                            role="system",
                            content=load_skill_context(selected_skill),
                        )
                    )
                else:
                    print(f"Selected skill: none ({selection_reason})")

            turn_history = turn_context + session_history

            response_object = await run_agent(
                user_query,
                turn_history,
                provider=llm,
                mcp_client=mcp_bridge,
            )

            if response_object.text:
                session_history.append(
                    InternalMessage(
                        role="assistant",
                        content=response_object.text,
                    )
                )

    finally:
        await mcp_bridge.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
