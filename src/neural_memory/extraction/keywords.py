"""Keyword extraction from text."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Common stop words (English + Vietnamese)
STOP_WORDS: frozenset[str] = frozenset(
    {
        # English
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "used",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "and",
        "but",
        "if",
        "or",
        "because",
        "until",
        "while",
        "this",
        "that",
        "these",
        "those",
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "ours",
        "ourselves",
        "you",
        "your",
        "yours",
        "yourself",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "what",
        "which",
        "who",
        "whom",
        # Vietnamese
        "và",
        "của",
        "là",
        "có",
        "được",
        "cho",
        "với",
        "này",
        "trong",
        "để",
        "các",
        "những",
        "một",
        "đã",
        "tôi",
        "bạn",
        "anh",
        "chị",
        "em",
        "ở",
        "tại",
        "khi",
        "thì",
        "mà",
        "nếu",
        "vì",
        "cũng",
        "như",
        "từ",
        "đến",
        "lại",
        "ra",
        "vào",
        "lên",
        "xuống",
        "rồi",
        "sẽ",
        "đang",
        "vẫn",
        "còn",
        "chỉ",
        "rất",
        "quá",
        "làm",
        "gì",
        "sao",
        "nào",
        "đâu",
        "ai",
        "bao",
        "nhiêu",
    }
)


@dataclass
class WeightedKeyword:
    """A keyword with an importance weight.

    Attributes:
        text: The keyword text (unigram or bi-gram)
        weight: Importance weight (0.0 - 1.5), higher = more important
    """

    text: str
    weight: float


def extract_weighted_keywords(text: str, min_length: int = 2) -> list[WeightedKeyword]:
    """
    Extract weighted keywords with bi-gram support.

    Scoring factors:
    - Position: earlier words score higher (1.0 → 0.5 linear decay)
    - Bi-grams: adjacent non-stop-word pairs get averaged weight * 1.2 boost

    Args:
        text: The text to extract from
        min_length: Minimum word length for unigrams

    Returns:
        List of WeightedKeyword sorted by weight descending
    """
    words = re.findall(r"\b[a-zA-ZÀ-ỹ]+\b", text.lower())

    # Filter to content words with original position
    filtered: list[tuple[str, int]] = [
        (w, i) for i, w in enumerate(words) if len(w) >= min_length and w not in STOP_WORDS
    ]

    if not filtered:
        return []

    total = len(filtered)
    weighted: dict[str, float] = {}

    # Unigrams with position decay (1.0 at start → 0.5 at end)
    for idx, (word, _orig_pos) in enumerate(filtered):
        position_weight = 1.0 - 0.5 * (idx / max(1, total - 1))
        weighted[word] = max(weighted.get(word, 0.0), position_weight)

    # Bi-grams from adjacent non-stop words within 3 original word positions
    for i in range(len(filtered) - 1):
        w1, p1 = filtered[i]
        w2, p2 = filtered[i + 1]
        if p2 - p1 <= 3:
            bigram = f"{w1} {w2}"
            bigram_weight = (weighted.get(w1, 0.5) + weighted.get(w2, 0.5)) / 2 * 1.2
            weighted[bigram] = max(weighted.get(bigram, 0.0), bigram_weight)

    results = [WeightedKeyword(text=k, weight=v) for k, v in weighted.items()]
    results.sort(key=lambda x: x.weight, reverse=True)
    return results


def extract_keywords(text: str, min_length: int = 2) -> list[str]:
    """
    Extract keywords from text, sorted by importance.

    Backward-compatible wrapper around extract_weighted_keywords().
    Returns bi-grams before unigrams, ordered by weight.

    Args:
        text: The text to extract from
        min_length: Minimum word length

    Returns:
        List of keyword strings
    """
    weighted = extract_weighted_keywords(text, min_length)
    return [kw.text for kw in weighted]
