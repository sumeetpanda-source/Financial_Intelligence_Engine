"""
Phase 1 multi-agent layer for the Financial Intelligence Engine.

The agents expose small, swappable contracts so the first implementation can run
locally while later versions can plug in FinBERT, TensorFlow, PyTorch, vector
databases, and hosted GenAI models.
"""

from .orchestrator_agent import OrchestratorAgent

__all__ = ["OrchestratorAgent"]
