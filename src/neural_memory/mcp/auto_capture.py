"""Auto-capture pattern detection for extracting memories from text."""

from __future__ import annotations

import re
from typing import Any

DECISION_PATTERNS = [
    r"(?:we |I )(?:decided|chose|selected|picked|opted)(?: to)?[:\s]+(.+?)(?:\.|$)",
    r"(?:the )?decision(?: is)?[:\s]+(.+?)(?:\.|$)",
    r"(?:we\'re |I\'m )going (?:to|with)[:\s]+(.+?)(?:\.|$)",
    r"let\'s (?:go with|use|choose)[:\s]+(.+?)(?:\.|$)",
]

ERROR_PATTERNS = [
    r"error[:\s]+(.+?)(?:\.|$)",
    r"failed[:\s]+(.+?)(?:\.|$)",
    r"bug[:\s]+(.+?)(?:\.|$)",
    r"(?:the )?issue (?:is|was)[:\s]+(.+?)(?:\.|$)",
    r"problem[:\s]+(.+?)(?:\.|$)",
]

TODO_PATTERNS = [
    r"(?:TODO|FIXME|HACK|XXX)[:\s]+(.+?)(?:\.|$)",
    r"(?:we |I )?(?:need to|should|must|have to)[:\s]+(.+?)(?:\.|$)",
    r"(?:remember to|don\'t forget to)[:\s]+(.+?)(?:\.|$)",
    r"(?:later|next)[:\s]+(.+?)(?:\.|$)",
]

FACT_PATTERNS = [
    r"(?:the |a )?(?:answer|solution|fix) (?:is|was)[:\s]+(.+?)(?:\.|$)",
    r"(?:it |this )(?:works|worked) because[:\s]+(.+?)(?:\.|$)",
    r"(?:the )?(?:key|important|note)[:\s]+(.+?)(?:\.|$)",
    r"(?:learned|discovered|found out)[:\s]+(.+?)(?:\.|$)",
]


def _detect_patterns(
    text: str,
    patterns: list[str],
    memory_type: str,
    confidence: float,
    priority: int,
    min_match_len: int,
    prefix: str = "",
) -> list[dict[str, Any]]:
    """Run a list of regex patterns and return detected memories."""
    detected: list[dict[str, Any]] = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) >= min_match_len:
                content = f"{prefix}{match.strip()}" if prefix else match.strip()
                detected.append({
                    "type": memory_type,
                    "content": content,
                    "confidence": confidence,
                    "priority": priority,
                })
    return detected


def analyze_text_for_memories(
    text: str,
    *,
    capture_decisions: bool = True,
    capture_errors: bool = True,
    capture_todos: bool = True,
    capture_facts: bool = True,
) -> list[dict[str, Any]]:
    """Analyze text and detect potential memories.

    Returns list of detected memories with type, content, and confidence.
    """
    detected: list[dict[str, Any]] = []
    text_lower = text.lower()

    if capture_decisions:
        detected.extend(
            _detect_patterns(text_lower, DECISION_PATTERNS, "decision", 0.8, 6, 10, "Decision: ")
        )

    if capture_errors:
        detected.extend(
            _detect_patterns(text_lower, ERROR_PATTERNS, "error", 0.85, 7, 10, "Error: ")
        )

    if capture_todos:
        detected.extend(
            _detect_patterns(text, TODO_PATTERNS, "todo", 0.75, 5, 5, "TODO: ")
        )

    if capture_facts:
        detected.extend(
            _detect_patterns(text_lower, FACT_PATTERNS, "fact", 0.7, 5, 15)
        )

    # Remove duplicates
    seen: set[str] = set()
    unique_detected: list[dict[str, Any]] = []
    for item in detected:
        content_key = item["content"][:50].lower()
        if content_key not in seen:
            seen.add(content_key)
            unique_detected.append(item)

    return unique_detected
