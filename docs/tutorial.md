# Scholar Bib Kit: Tutorial

This tutorial shows you how to use `scholar-bib-kit` to automatically repair and standardize messy BibTeX files.

## Command Line Interface

The simplest way to use the kit is via the CLI. It reads a `.bib` file, matches entries against Crossref, and outputs a cleaned `.bib` file.

```bash
scholar-bib fix messy.bib --output fixed.bib
```

### Options

- `--output`, `-o`: Where to save the fixed file. Defaults to `input_file_fixed.bib`.
- `--no-fuzzy`: Disable fuzzy matching (searching by title/author) if a DOI is missing. Speeds up the process if you only want to verify existing DOIs.
- `--overwrite`: Overwrite existing fields with authoritative data from Crossref. By default, it only fills in missing fields.

```bash
scholar-bib fix messy.bib --no-fuzzy --overwrite
```

## Python API

You can also use the kit programmatically:

```python
from pathlib import Path
from scholar_bib.parser import BibParser
from scholar_bib.repair import RepairEngine

parser = BibParser(Path("messy.bib"))
entries = parser.read()

engine = RepairEngine()
for entry in entries:
    engine.repair_entry(entry, fuzzy=True)

parser.write(Path("fixed.bib"))
```
