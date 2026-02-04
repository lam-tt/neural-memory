"""Core data models for NeuralMemory."""

from neural_memory.core.brain import Brain, BrainConfig
from neural_memory.core.fiber import Fiber
from neural_memory.core.memory_types import (
    Confidence,
    MemoryType,
    Priority,
    Provenance,
    TypedMemory,
    suggest_memory_type,
)
from neural_memory.core.neuron import Neuron, NeuronState, NeuronType
from neural_memory.core.project import MemoryScope, Project
from neural_memory.core.synapse import Direction, Synapse, SynapseType

__all__ = [
    # Brain
    "Brain",
    "BrainConfig",
    # Memory structures
    "Fiber",
    "Neuron",
    "NeuronState",
    "NeuronType",
    "Synapse",
    "SynapseType",
    "Direction",
    # Memory types (MemoCore integration)
    "MemoryType",
    "Priority",
    "Confidence",
    "Provenance",
    "TypedMemory",
    "suggest_memory_type",
    # Project scoping
    "Project",
    "MemoryScope",
]
