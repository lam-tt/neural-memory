"""API routes for NeuralMemory server."""

from neural_memory.server.routes.brain import router as brain_router
from neural_memory.server.routes.memory import router as memory_router

__all__ = ["memory_router", "brain_router"]
