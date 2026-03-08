"""Tests for formatting, citation, and similarity utilities."""

from __future__ import annotations

import pytest

from models.paper import Paper
from utils.formatting import truncate, format_authors, format_categories, format_saved_date
from utils.citations import to_bibtex, to_plain_citation, to_markdown_citation
from services.similarity import find_related
from services.arxiv import _extract_arxiv_id


# ── formatting ───────────────────────────────────────────────────

class TestTruncate:
    def test_short_string(self):
        assert truncate("hello", 10) == "hello"

    def test_exact_limit(self):
        assert truncate("hello", 5) == "hello"

    def test_over_limit(self):
        result = truncate("hello world", 8)
        assert result.endswith("...")
        assert len(result) <= 8

    def test_empty_string(self):
        assert truncate("", 10) == ""


class TestFormatAuthors:
    def test_single_author(self):
        assert format_authors(["Alice"]) == "Alice"

    def test_multiple_within_limit(self):
        assert format_authors(["Alice", "Bob"], limit=3) == "Alice, Bob"

    def test_more_than_limit(self):
        result = format_authors(["Alice", "Bob", "Charlie", "Diana"], limit=2)
        assert result == "Alice, Bob, et al."

    def test_empty(self):
        assert format_authors([]) == "Unknown"


class TestFormatCategories:
    def test_normal(self):
        assert format_categories(["cs.AI", "cs.CL"]) == "cs.AI, cs.CL"

    def test_empty(self):
        assert format_categories([]) == "N/A"

    def test_limit(self):
        cats = ["a", "b", "c", "d"]
        assert format_categories(cats, limit=2) == "a, b"


class TestFormatSavedDate:
    def test_iso_date(self):
        assert format_saved_date("2024-03-15T12:30:00Z") == "2024-03-15"

    def test_empty(self):
        assert format_saved_date("") == "Unknown"


# ── citations ────────────────────────────────────────────────────

@pytest.fixture()
def paper() -> Paper:
    return Paper(
        arxiv_id="2401.12345",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        summary="The Transformer architecture.",
        published="2017-06-12T17:57:34Z",
        categories=["cs.CL", "cs.AI"],
        arxiv_url="https://arxiv.org/abs/2401.12345",
        pdf_url="https://arxiv.org/pdf/2401.12345",
        doi="10.1234/test",
    )


class TestBibtex:
    def test_basic_structure(self, paper: Paper):
        bib = to_bibtex(paper)
        assert bib.startswith("@article{")
        assert "vaswani2017" in bib
        assert "Attention Is All You Need" in bib
        assert "archivePrefix = {arXiv}" in bib

    def test_doi_included(self, paper: Paper):
        bib = to_bibtex(paper)
        assert "doi       = {10.1234/test}" in bib

    def test_no_doi(self):
        p = Paper(
            arxiv_id="1234.5678", title="Test", authors=["A"],
            published="2020-01-01", categories=["cs.AI"],
            arxiv_url="https://arxiv.org/abs/1234.5678",
        )
        bib = to_bibtex(p)
        assert "doi" not in bib

    def test_special_chars_escaped(self):
        p = Paper(
            arxiv_id="1234.5678", title="A & B # C % D",
            authors=["Author"], published="2020-01-01",
            categories=["cs.AI"], arxiv_url="https://arxiv.org/abs/1234.5678",
        )
        bib = to_bibtex(p)
        assert r"A \& B \# C \% D" in bib

    def test_underscores_and_braces_escaped(self):
        p = Paper(
            arxiv_id="1234.5678", title="E_x {F} G",
            authors=["Author"], published="2020-01-01",
            categories=["cs.AI"], arxiv_url="https://arxiv.org/abs/1234.5678",
        )
        bib = to_bibtex(p)
        assert r"E\_x \{F\} G" in bib

    def test_backslash_escaped_without_corruption(self):
        p = Paper(
            arxiv_id="1234.5678", title=r"A\B",
            authors=["Author"], published="2020-01-01",
            categories=["cs.AI"], arxiv_url="https://arxiv.org/abs/1234.5678",
        )
        bib = to_bibtex(p)
        assert r"A\textbackslash{}B" in bib


class TestPlainCitation:
    def test_format(self, paper: Paper):
        cite = to_plain_citation(paper)
        assert "Ashish Vaswani" in cite
        assert "(2017)" in cite
        assert "arXiv:2401.12345" in cite
        assert "doi:10.1234/test" in cite

    def test_no_doi(self):
        p = Paper(
            arxiv_id="1234.5678", title="Test", authors=["A"],
            published="2020-01-01", categories=[], arxiv_url="",
        )
        cite = to_plain_citation(p)
        assert "doi" not in cite


class TestMarkdownCitation:
    def test_format(self, paper: Paper):
        cite = to_markdown_citation(paper)
        assert "**Attention Is All You Need**" in cite
        assert "[arXiv:2401.12345]" in cite
        assert "(2017)" in cite


# ── similarity ───────────────────────────────────────────────────

class TestFindRelated:
    def test_similar_papers(self):
        target = Paper(
            arxiv_id="0001", title="Deep learning for NLP",
            summary="We use deep learning techniques for natural language processing tasks.",
            categories=["cs.CL"], arxiv_url="",
        )
        similar = Paper(
            arxiv_id="0002", title="NLP with neural networks",
            summary="Neural network models applied to language understanding.",
            categories=["cs.CL"], arxiv_url="",
        )
        unrelated = Paper(
            arxiv_id="0003", title="Galaxy formation in the early universe",
            summary="Observations of galaxy clusters using radio telescopes.",
            categories=["astro-ph"], arxiv_url="",
        )

        results = find_related(target, [similar, unrelated], top_k=2)
        assert len(results) >= 1
        # The NLP paper should rank higher than the astrophysics paper
        ids = [p.arxiv_id for p, _ in results]
        assert ids[0] == "0002"

    def test_empty_candidates(self):
        target = Paper(arxiv_id="0001", title="Test", arxiv_url="")
        assert find_related(target, []) == []

    def test_scores_are_bounded(self):
        target = Paper(
            arxiv_id="0001", title="Machine learning", summary="ML stuff",
            categories=["cs.LG"], arxiv_url="",
        )
        candidate = Paper(
            arxiv_id="0002", title="Machine learning too", summary="Also ML stuff",
            categories=["cs.LG"], arxiv_url="",
        )
        results = find_related(target, [candidate])
        for _, score in results:
            assert 0.0 <= score <= 1.0


# ── arXiv ID extraction ─────────────────────────────────────────

class TestExtractArxivId:
    def test_modern_id(self):
        assert _extract_arxiv_id("https://arxiv.org/abs/2401.12345v2") == "2401.12345"

    def test_bare_modern_id(self):
        assert _extract_arxiv_id("2401.12345") == "2401.12345"

    def test_legacy_id_url(self):
        assert _extract_arxiv_id("https://arxiv.org/abs/hep-th/9901001") == "hep-th/9901001"

    def test_bare_legacy_id(self):
        assert _extract_arxiv_id("hep-th/9901001") == "hep-th/9901001"

    def test_legacy_id_with_version(self):
        assert _extract_arxiv_id("cond-mat/0001234v3") == "cond-mat/0001234"

    def test_five_digit_modern_id(self):
        assert _extract_arxiv_id("2301.00001") == "2301.00001"

    def test_dotted_legacy_id(self):
        assert _extract_arxiv_id("math.AG/0309136") == "math.AG/0309136"

    def test_dotted_legacy_id_url(self):
        assert _extract_arxiv_id("https://arxiv.org/abs/math.AG/0309136v2") == "math.AG/0309136"
