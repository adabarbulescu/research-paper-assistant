"""Lightweight TF-IDF cosine similarity using only the Python standard library."""

from __future__ import annotations

import math
import re
from collections import Counter

from models.paper import Paper

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Common English stopwords to filter out
_STOPWORDS = frozenset(
    "a an and are as at be but by for from has have in is it its of on or"
    " that the this to was were will with we they not are can do".split()
)


def _tokenize(text: str) -> list[str]:
    """Lowercase, extract alpha-numeric tokens, remove stopwords."""
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


def _paper_text(paper: Paper) -> str:
    """Build the text representation of a paper for similarity comparison."""
    parts = [paper.title, paper.title, paper.summary]  # title weighted 2x
    parts.extend(paper.categories)
    return " ".join(parts)


def _build_tfidf(documents: list[list[str]]) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Compute TF-IDF vectors for a list of tokenized documents.

    Returns (tfidf_vectors, idf_dict).
    """
    n = len(documents)
    if n == 0:
        return [], {}

    # Document frequency: how many documents contain each term
    df: Counter[str] = Counter()
    for tokens in documents:
        df.update(set(tokens))

    # IDF with smoothing: log((n + 1) / (df + 1)) + 1
    idf = {term: math.log((n + 1) / (count + 1)) + 1 for term, count in df.items()}

    # TF-IDF for each document
    vectors: list[dict[str, float]] = []
    for tokens in documents:
        tf = Counter(tokens)
        total = len(tokens) or 1
        vec = {term: (count / total) * idf.get(term, 0) for term, count in tf.items()}
        vectors.append(vec)

    return vectors, idf


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vectors."""
    # Only iterate over shared keys
    shared_keys = vec_a.keys() & vec_b.keys()
    if not shared_keys:
        return 0.0

    dot = sum(vec_a[k] * vec_b[k] for k in shared_keys)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


def find_related(target: Paper, candidates: list[Paper], top_k: int = 5) -> list[tuple[Paper, float]]:
    """Find the most similar papers to `target` from `candidates`.

    Returns a list of (paper, similarity_score) tuples, sorted by score descending.
    Papers with zero similarity are excluded.
    """
    if not candidates:
        return []

    # Build documents: target first, then candidates
    all_papers = [target, *candidates]
    documents = [_tokenize(_paper_text(p)) for p in all_papers]

    vectors, _ = _build_tfidf(documents)

    target_vec = vectors[0]
    results: list[tuple[Paper, float]] = []

    for i, paper in enumerate(candidates, start=1):
        score = _cosine_similarity(target_vec, vectors[i])
        if score > 0:
            results.append((paper, round(score, 4)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
