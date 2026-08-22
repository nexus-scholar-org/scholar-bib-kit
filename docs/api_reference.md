# Scholar Bib Kit: API Reference

This document provides the API contracts for the core components of `scholar-bib-kit`.

## `BibParser`
Handles reading and writing BibTeX files safely.

```python
from scholar_bib.parser import BibParser
from pathlib import Path

parser = BibParser(Path("my_library.bib"))
entries = parser.read()
# ... modify entries ...
parser.write(Path("my_library_fixed.bib"))
```

## `CrossrefValidator`
Fetches authoritative metadata from Crossref with rate limiting and timeout handling.

```python
from scholar_bib.validator import CrossrefValidator

validator = CrossrefValidator()

# Get by DOI
data = validator.get_by_doi("10.1234/example")

# Fuzzy match by title and author
data = validator.fuzzy_match("The Title of Paper", "Doe, John")
```

## `RepairEngine`
Merges messy BibTeX entries with authoritative Crossref data.

```python
from scholar_bib.repair import RepairEngine

engine = RepairEngine()

entry = {
    "ID": "doe2023",
    "ENTRYTYPE": "article",
    "title": "Messy Title",
    "author": "John Doe",
    "doi": "10.1234/example"
}

# Repair the entry in-place
success = engine.repair_entry(entry, fuzzy=True, overwrite=False)
```

## Models
Strictly validated data structures.

- `BibEntry`: Validates the structure of a BibTeX entry.
- `RepairStats`: Used to track repair metrics.
