import bibtexparser
from pathlib import Path
from bibtexparser.library import Library

class BibParser:
    @staticmethod
    def load(filepath: Path | str) -> Library:
        """Load a BibTeX file into a Library object."""
        return bibtexparser.parse_file(str(filepath))

    @staticmethod
    def save(library: Library, filepath: Path | str) -> None:
        """Save a Library object to a BibTeX file."""
        bibtexparser.write_file(str(filepath), library)
