import json
import re
from typing import Dict, Optional, Tuple

from agent.models import InternalMessage
from agent.providers.base import LLMProvider
from agent.skills import SkillDefinition


def _normalize_skill_token(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace(" ", "-")


def _extract_explicit_skill(user_query: str, skills: Dict[str, SkillDefinition]) -> Optional[SkillDefinition]:
    patterns = [
        r"\buse (?:the )?(?P<name>[a-zA-Z0-9_-]+) skill\b",
        r"\buse skill (?P<name>[a-zA-Z0-9_-]+)\b",
        r"\bwith (?:the )?(?P<name>[a-zA-Z0-9_-]+) skill\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, user_query, flags=re.IGNORECASE)
        if not match:
            continue
        candidate = _normalize_skill_token(match.group("name"))
        if candidate in skills:
            return skills[candidate]

    return None


def _parse_selection_response(
    raw_text: Optional[str],
    skills: Dict[str, SkillDefinition],
) -> Tuple[Optional[SkillDefinition], str]:
    if not raw_text:
        return None, "no selector output"

    raw_text = raw_text.strip()
    if raw_text in {"none", "null"}:
        return None, "selector chose none"

    try:
        payload = json.loads(raw_text)
        skill_name = _normalize_skill_token(str(payload.get("skill", "none")))
        reason = str(payload.get("reason", "")).strip() or "selector returned JSON"
        if skill_name == "none":
            return None, reason
        if skill_name in skills:
            return skills[skill_name], reason
    except json.JSONDecodeError:
        pass

    lowered = _normalize_skill_token(raw_text)
    if lowered in skills:
        return skills[lowered], "selector returned exact skill name"

    for skill_name, skill in skills.items():
        if skill_name in lowered:
            return skill, "selector mentioned skill name in free text"

    return None, f"unparsed selector output: {raw_text}"


async def select_skill_for_turn(
    user_query: str,
    skills: Dict[str, SkillDefinition],
    provider: LLMProvider,
) -> Tuple[Optional[SkillDefinition], str]:
    if not skills:
        return None, "no installed skills"

    explicit_skill = _extract_explicit_skill(user_query, skills)
    if explicit_skill:
        return explicit_skill, "explicit user selection"

    skill_lines = [f"- {skill.name}: {skill.description}" for skill in skills.values()]
    selector_messages = [
        InternalMessage(
            role="system",
            content=(
                "You are selecting one local skill for an agent turn. "
                "Choose at most one skill if it is clearly useful for the user request. "
                "Return JSON only with the shape {\"skill\": \"<name-or-none>\", \"reason\": \"<short reason>\"}. "
                "If no skill is clearly needed, return {\"skill\": \"none\", \"reason\": \"...\"}."
            ),
        ),
        InternalMessage(
            role="user",
            content=(
                "User request:\n"
                f"{user_query}\n\n"
                "Available skills:\n"
                + "\n".join(skill_lines)
            ),
        ),
    ]

    try:
        response = await provider.generate(selector_messages, tools=None)
    except Exception as exc:
        return None, f"selector failed: {exc}"

    return _parse_selection_response(response.text, skills)
