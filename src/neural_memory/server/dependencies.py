"""Shared dependencies for API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from neural_memory.core.brain import Brain
from neural_memory.storage.base import NeuralStorage


async def get_storage() -> NeuralStorage:
    """
    Dependency to get storage instance.

    This is overridden by the application at startup.
    """
    raise NotImplementedError("Storage not configured")


async def get_brain(
    brain_id: Annotated[str, Header(alias="X-Brain-ID")],
    storage: Annotated[NeuralStorage, Depends(get_storage)],
) -> Brain:
    """Dependency to get and validate brain from header."""
    brain = await storage.get_brain(brain_id)
    if brain is None:
        raise HTTPException(status_code=404, detail=f"Brain {brain_id} not found")

    # Set brain context
    storage.set_brain(brain_id)  # type: ignore
    return brain
