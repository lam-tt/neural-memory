"""Keyword extraction from text."""

from __future__ import annotations

import re

# Common stop words (English + Vietnamese)
STOP_WORDS: frozenset[str] = frozenset({
    # English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "just", "and", "but",
    "if", "or", "because", "until", "while", "this", "that", "these",
    "those", "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "it", "its", "itself", "they",
    "them", "their", "theirs", "what", "which", "who", "whom",
    # Vietnamese
    "và", "của", "là", "có", "được", "cho", "với", "này", "trong", "để",
    "các", "những", "một", "đã", "tôi", "bạn", "anh", "chị", "em", "ở",
    "tại", "khi", "thì", "mà", "nếu", "vì", "cũng", "như", "từ", "đến",
    "lại", "ra", "vào", "lên", "xuống", "rồi", "sẽ", "đang", "vẫn",
    "còn", "chỉ", "rất", "quá", "làm", "gì", "sao", "nào", "đâu", "ai",
    "bao", "nhiêu",
})


def extract_keywords(text: str, min_length: int = 2) -> list[str]:
    """
    Extract keywords from text (simple word extraction).

    This is a basic keyword extractor. For better results,
    consider using TF-IDF or other NLP techniques.

    Args:
        text: The text to extract from
        min_length: Minimum word length

    Returns:
        List of keywords
    """
    # Tokenize (simple split)
    words = re.findall(r"\b[a-zA-ZÀ-ỹ]+\b", text.lower())

    # Filter
    keywords = [w for w in words if len(w) >= min_length and w not in STOP_WORDS]

    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique.append(word)

    return unique
