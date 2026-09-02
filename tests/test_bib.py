"""Unit tests for scholar-bib-kit."""

from pathlib import Path
import pytest

from scholar_bib.parser import BibParser
from scholar_bib.linter import BibLinter
from scholar_bib.deduplicator import BibDeduplicator


@pytest.fixture
def sample_bib_file(tmp_path):
    content = (
        "@article{vaswani2017attention,\n"
        "  title={Attention Is All You Need},\n"
        "  author={Vaswani, Ashish and Shazeer, Noam},\n"
        "  year={2017},\n"
        "  doi={10.5555/3295222.3295349}\n"
        "}\n\n"
        "@article{vaswani2017dup,\n"
        "  title={Attention Is All You Need},\n"
        "  author={Vaswani, Ashish},\n"
        "  year={2017},\n"
        "  doi={10.5555/3295222.3295349}\n"
        "}\n\n"
        "@article{devlin2018bert,\n"
        "  title={BERT: Pre-training of Deep Bidirectional Transformers},\n"
        "  author={Devlin, Jacob},\n"
        "  year={2018},\n"
        "  doi={10.18653/v1/N19-1423}\n"
        "}\n"
    )
    bib_path = tmp_path / "test.bib"
    bib_path.write_text(content, encoding="utf-8")
    return bib_path


def test_bib_parser_and_linter(sample_bib_file, tmp_path):
    library = BibParser.load(sample_bib_file)
    assert len(library.entries) == 3

    # Lint
    linted = BibLinter.lint(library, generate_keys=True)
    out_file = tmp_path / "linted.bib"
    BibParser.save(linted, out_file)
    assert out_file.exists()

    saved_lib = BibParser.load(out_file)
    assert len(saved_lib.entries) == 3


def test_bib_deduplicator(sample_bib_file, tmp_path):
    library = BibParser.load(sample_bib_file)
    assert len(library.entries) == 3

    deduped = BibDeduplicator.dedup(library)
    assert len(deduped.entries) == 2

    out_file = tmp_path / "deduped.bib"
    BibParser.save(deduped, out_file)
    assert out_file.exists()
