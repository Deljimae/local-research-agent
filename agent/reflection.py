import json
from config import client, LLM_PROVIDER, LLM_MODEL, ANTHROPIC_API_KEY


REFLECTION_PROMPT = """
You are a 'Memory Secretary' for an AI Agent. Your job is to analyze the conversation history and extract 3 types of long-term memories.

1. SEMANTIC (Facts): Permanent info about the user (name, location, preferences, job).
2. EPISODIC (Events): Notable successes or failures. What happened? Did a tool work or fail?
3. PROCEDURAL (Rules): Best practices or workflows. How should the agent behave next time? (e.g., 'Always use Celsius for this user').

Output ONLY a valid JSON object with this structure:
{
  "semantic": [{"fact": "...", "category": "..."}],
  "episodic": [{"event": "...", "outcome": "..."}],
  "procedural": [{"rule": "...", "context": "..."}]
}

If no new information is found for a category, return an empty list for it.
"""


def _as_role_content(history):
    return [{"role": m.role, "content": m.content} for m in history]


def _reflect_openai(api_history):
    response = client.responses.create(
        model=LLM_MODEL or "gpt-4o-mini",
        input=api_history + [{"role": "user", "content": REFLECTION_PROMPT}],
    )
    return response.output_text.strip()


def _reflect_anthropic(api_history):
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")

    from anthropic import Anthropic

    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

    transcript_lines = []
    for item in api_history:
        role = item["role"].upper()
        content = item.get("content", "")
        transcript_lines.append(f"{role}: {content}")

    transcript = "\n".join(transcript_lines)

    response = anthropic_client.messages.create(
        model=LLM_MODEL or "claude-3-5-sonnet-latest",
        max_tokens=1024,
        system=REFLECTION_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Conversation history:\n\n{transcript}\n\nReturn only the JSON object.",
            }
        ],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip()


def reflect_on_session(chat_history):
    api_history = _as_role_content(chat_history)

    try:
        if LLM_PROVIDER == "anthropic":
            raw_text = _reflect_anthropic(api_history)
        else:
            raw_text = _reflect_openai(api_history)

        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        return json.loads(raw_text)
    except Exception as e:
        print(f"Reflection Parsing Error: {e}")
        return {"semantic": [], "episodic": [], "procedural": []}
