from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict


@dataclass
class InternalMessage:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_call_id: Optional[str] = None # For tool results
    tool_calls: List[ToolCall] = field(default_factory=list)

@dataclass
class AgentResponse:
    text: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
