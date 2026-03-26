from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


@dataclass
class SkillDefinition:
    name: str
    description: str
    path: Path
    assets: List[str] = field(default_factory=list)


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_list_value(value: str) -> List[str]:
    value = value.strip()
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(part.strip()) for part in inner.split(",") if part.strip()]
    return [_strip_quotes(part.strip()) for part in value.split(",") if part.strip()]


def _split_frontmatter(text: str) -> Tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text

    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text

    raw_frontmatter = parts[0][4:]
    body = parts[1]
    metadata = {}
    current_list_key = None

    for raw_line in raw_frontmatter.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        stripped = line.strip()
        if stripped.startswith("- ") and current_list_key:
            metadata.setdefault(current_list_key, []).append(_strip_quotes(stripped[2:].strip()))
            continue

        if ":" not in line:
            current_list_key = None
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if not value:
            metadata[key] = []
            current_list_key = key
            continue

        current_list_key = None
        if key == "assets":
            metadata[key] = _parse_list_value(value)
        else:
            metadata[key] = _strip_quotes(value)

    return metadata, body.strip()


def discover_skills() -> Dict[str, SkillDefinition]:
    skills: Dict[str, SkillDefinition] = {}

    if not SKILLS_DIR.exists():
        return skills

    for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        metadata, _ = _split_frontmatter(text)
        name = metadata.get("name")
        description = metadata.get("description")
        assets = metadata.get("assets", [])

        if not name or not description:
            continue

        skills[name] = SkillDefinition(
            name=name,
            description=description,
            path=skill_file,
            assets=assets,
        )

    return skills


def build_available_skills_context(skills: Dict[str, SkillDefinition]) -> str:
    if not skills:
        return "No local skills are installed."

    lines = [
        "AVAILABLE SKILLS:",
        "These are reusable procedures. Do not assume one is active unless it has been explicitly selected for this turn.",
        "If the user explicitly asks for a skill, follow it. Otherwise, only use an active skill if one is supplied in the context.",
        "",
    ]

    for skill in skills.values():
        lines.append(f"- {skill.name}: {skill.description}")

    return "\n".join(lines)


def load_skill_context(skill: SkillDefinition) -> str:
    text = skill.path.read_text(encoding="utf-8")
    _, body = _split_frontmatter(text)

    sections = [
        f"ACTIVE SKILL: {skill.name}",
        f"DESCRIPTION: {skill.description}",
        "Follow these skill instructions for this turn:",
        body,
    ]

    for asset_name in skill.assets:
        asset_path = skill.path.parent / asset_name
        if not asset_path.exists() or not asset_path.is_file():
            continue
        asset_text = asset_path.read_text(encoding="utf-8").strip()
        if not asset_text:
            continue
        sections.append(f"ASSET: {asset_name}\n{asset_text}")

    return "\n\n".join(section for section in sections if section.strip())
