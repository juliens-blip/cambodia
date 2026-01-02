"""Text postprocessing helpers for UI display."""
from __future__ import annotations

import re
from typing import Iterable


def _collapse_split_lines(text: str) -> str:
    """Collapse lines that were split into single characters."""
    if not isinstance(text, str) or "\n" not in text:
        return text

    lines = text.splitlines()
    if not lines:
        return text

    rebuilt = []
    buffer = []

    def flush_buffer() -> None:
        if not buffer:
            return
        if len(buffer) >= 6 and all(len(item) <= 4 and " " not in item for item in buffer):
            rebuilt.append("".join(buffer))
        else:
            rebuilt.extend(buffer)
        buffer.clear()

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            flush_buffer()
            rebuilt.append("")
            continue
        if len(stripped) <= 4 and " " not in stripped:
            buffer.append(stripped)
            continue
        flush_buffer()
        rebuilt.append(line)

    flush_buffer()
    return "\n".join(rebuilt)


def postprocess_text(text: str) -> str:
    """Normalize malformed sequences and ranges in AI output."""
    if not isinstance(text, str):
        return text

    cleaned = text.replace("\uFFFD", "")
    cleaned = _collapse_split_lines(cleaned)

    # Fix glued "by2030" and malformed CAGR tokens.
    cleaned = re.sub(r"\bby\s*(\d{4})\b", r"by \1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\bCAGR\s*([0-9]+(?:\.[0-9]+)?)%?\b",
        r"CAGR \1%",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"by\s*(\d{4})\s*\(\s*CAGR\s*([0-9]+(?:\.[0-9]+)?)%?\s*\)?",
        r"by \1 (CAGR \2%)",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove spaced-out digits/words like "1 , 800" or "s t a b l e".
    cleaned = re.sub(r"(\d)\s*,\s*(\d)", r"\1,\2", cleaned)
    cleaned = re.sub(r"(\d)\s*\.\s*(\d)", r"\1.\2", cleaned)
    cleaned = re.sub(
        r"\b(?:[A-Za-z]\s+){3,}[A-Za-z]\b",
        lambda m: m.group(0).replace(" ", ""),
        cleaned,
    )
    cleaned = re.sub(
        r"\b(?:\d\s+){2,}\d\b",
        lambda m: m.group(0).replace(" ", ""),
        cleaned,
    )

    # Normalize numeric ranges with corrupted separators.
    cleaned = re.sub(
        r"(\d[\d,\.]*)\s*(?:\?|\-|~|\u2013|\u2014)\s*\$?\s*(\d[\d,\.]*)",
        r"\1-\2",
        cleaned,
    )
    cleaned = re.sub(
        r"(\d[\d,\.]*)\s*to\s*\$?\s*(\d[\d,\.]*)",
        r"\1-\2",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"(\d[\d,\.]*)\s*(\d[\d,\.]*)\s*/\s*(ton|kg|t)\b",
        r"\1-\2/\3",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Collapse duplicated "vs" segments like "6.3kvs6.3kvs2k".
    cleaned = re.sub(
        r"(\b[\d\.]+k)vs\1vs(\b[\d\.]+k)",
        r"\1 vs \2",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"(\b[\d\.]+k)\s*vs\s*\1", r"\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*vs\s*", " vs ", cleaned, flags=re.IGNORECASE)

    # Remove repeated corrupted question marks.
    cleaned = re.sub(r"\?{2,},", ",", cleaned)
    cleaned = re.sub(r"\?{2,}", "", cleaned)

    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


def compact_sentences(text: str, max_sentences: int = 3) -> str:
    """Return the first N sentences for compact display."""
    if not isinstance(text, str):
        return text
    content = postprocess_text(text)
    sentences = re.split(r"(?<=[.!?])\s+", content)
    return " ".join(sentences[:max_sentences]).strip()


def unique_lines(lines: Iterable[str]) -> list[str]:
    """Remove exact duplicate lines while preserving order."""
    seen = set()
    deduped = []
    for line in lines:
        key = line.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(line)
    return deduped
