"""
Shared schemas for Phase 1 agents.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class EvidenceItem:
    """A source item used by an agent."""

    source: str
    text: str
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Standard response shape for every agent."""

    agent_name: str
    status: str
    summary: str
    data: Dict[str, Any] = field(default_factory=dict)
    evidence: List[EvidenceItem] = field(default_factory=list)
    confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)

