"""Small retrieval index over a folder of markdown write-ups.

Method: TF-IDF cosine similarity (lexical, not neural embeddings), pure Python.
Flow: split files into chunks -> weight words by how rare they are -> turn each chunk and
the query into a normalized word-weight vector -> rank chunks by dot product.
Limitation: it matches words, not meaning ("re-enter" will not match "reentrancy"). Swap the
vector step for a neural embedding model if that matters; the rest stays the same.
"""

import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

STOP = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "is", "are", "be",
    "it", "this", "that", "with", "as", "by", "from", "at", "if", "when",
}


def tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9_]+", text.lower()) if w not in STOP and len(w) > 1]


@dataclass
class Chunk:
    source: str
    text: str


def chunk_file(name: str, text: str, max_chars: int = 900) -> list[Chunk]:
    """Split on blank lines; keep the title line on every chunk so it carries context."""
    title, _, body = text.partition("\n")
    chunks, current = [], ""
    for para in re.split(r"\n\s*\n", body.strip()):
        if current and len(current) + len(para) > max_chars:
            chunks.append(Chunk(name, f"{title}\n{current}"))
            current = ""
        current = f"{current}\n{para}".strip()
    if current:
        chunks.append(Chunk(name, f"{title}\n{current}"))
    return chunks


class Index:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        counts = [Counter(tokens(c.text)) for c in chunks]
        df = Counter(w for c in counts for w in c)
        n = len(chunks)
        self.idf = {w: math.log((n + 1) / (d + 1)) + 1 for w, d in df.items()}
        self.vectors = [self._normalize(c) for c in counts]

    def _normalize(self, counts: Counter) -> dict[str, float]:
        vec = {w: tf * self.idf[w] for w, tf in counts.items() if w in self.idf}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {w: v / norm for w, v in vec.items()}

    @classmethod
    def build(cls, folder: str | Path) -> "Index":
        chunks = []
        for p in sorted(Path(folder).glob("*.md")):
            chunks += chunk_file(p.name, p.read_text())
        return cls(chunks)

    def search(self, query: str, k: int = 3) -> list[Chunk]:
        q = self._normalize(Counter(tokens(query)))
        scored = [(sum(w * v.get(t, 0.0) for t, w in q.items()), i) for i, v in enumerate(self.vectors)]
        best = sorted((s for s in scored if s[0] > 0), reverse=True)[:k]
        return [self.chunks[i] for _, i in best]


def from_env() -> "Index | None":
    """AGENT_RAG=1 turns retrieval on; AGENT_RAG_DIR picks the folder (default: knowledge)."""
    if os.environ.get("AGENT_RAG") != "1":
        return None
    return Index.build(os.environ.get("AGENT_RAG_DIR", "knowledge"))
