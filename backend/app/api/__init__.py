"""API routers for Relay."""

from .health import router as health_router
from .demo import router as demo_router
from .retrieval import router as retrieval_router
from .context import router as context_router

__all__ = ["health_router", "demo_router", "retrieval_router", "context_router"]
