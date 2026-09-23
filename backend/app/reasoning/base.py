"""Reasoning provider interface decoupling Relay from specific model implementations."""

from abc import ABC, abstractmethod
from app.context.assembled_context import AssembledContext
from app.reasoning.models import ReasoningResult


class ReasoningProvider(ABC):
    """
    Abstract interface for evidence-grounded reasoning over AssembledContext.

    Separation of Concerns:
    - Never calls Moss directly (always receives AssembledContext).
    - Never bypasses ContextAssembler.
    - Operates dynamically over arbitrary queries without hardcoded Q&A tables.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name identifier of this reasoning provider."""
        pass

    @abstractmethod
    async def reason(self, context: AssembledContext) -> ReasoningResult:
        """
        Execute evidence-grounded reasoning over an AssembledContext.

        Args:
            context: Complete structured AssembledContext case file.

        Returns:
            ReasoningResult containing claims, next steps, safety, and citations.
        """
        pass
