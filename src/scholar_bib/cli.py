import typer
from pathlib import Path
from rich.console import Console

from .parser import BibParser
from .linter import BibLinter
from .deduplicator import BibDeduplicator
from .resolver import BibResolver

app = typer.Typer(help="Scholar Bib Kit: Manage, lint, deduplicate, and resolve BibTeX databases.")
console = Console()

@app.command("lint")
def lint(
    input_file: Path = typer.Argument(..., help="Path to the input BibTeX file"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Path to save the linted file (defaults to overwrite)"),
    generate_keys: bool = typer.Option(False, "--generate-keys", help="Standardize all keys to AuthorYear format")
):
    """Lint a BibTeX file: wrap titles in double braces and optionally standardize keys."""
    if not output_file:
        output_file = input_file
        
    console.print(f"[cyan]Loading {input_file}...[/cyan]")
    library = BibParser.load(input_file)
    
    console.print(f"[cyan]Linting {len(library.entries)} entries...[/cyan]")
    linted_library = BibLinter.lint(library, generate_keys=generate_keys)
    
    BibParser.save(linted_library, output_file)
    console.print(f"[bold green]Successfully saved linted database to {output_file}[/bold green]")

@app.command("merge")
def merge(
    input_files: list[Path] = typer.Argument(..., help="List of input BibTeX files to merge"),
    output_file: Path = typer.Option(Path("merged.bib"), "--output", "-o", help="Path to save the merged output file"),
    dedup: bool = typer.Option(True, "--dedup/--no-dedup", help="Deduplicate entries after merging")
):
    """Merge multiple BibTeX files into a single database."""
    if not input_files:
        console.print("[yellow]No input files provided.[/yellow]")
        raise typer.Exit(1)
        
    merged_library = None
    
    for file in input_files:
        console.print(f"[cyan]Loading {file}...[/cyan]")
        lib = BibParser.load(file)
        if merged_library is None:
            merged_library = lib
        else:
            for block in lib.blocks:
                merged_library.add(block)
                
    console.print(f"[cyan]Merged into {len(merged_library.entries)} total entries.[/cyan]")
    
    if dedup:
        console.print("[cyan]Deduplicating entries...[/cyan]")
        merged_library = BibDeduplicator.dedup(merged_library)
        console.print(f"[cyan]Remaining unique entries: {len(merged_library.entries)}[/cyan]")
        
    BibParser.save(merged_library, output_file)
    console.print(f"[bold green]Successfully saved merged database to {output_file}[/bold green]")

@app.command("dedup")
def dedup(
    input_file: Path = typer.Argument(..., help="Path to the input BibTeX file"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Path to save the deduplicated file (defaults to overwrite)")
):
    """Deduplicate entries in a single BibTeX file based on DOI and title matches."""
    if not output_file:
        output_file = input_file
        
    console.print(f"[cyan]Loading {input_file}...[/cyan]")
    library = BibParser.load(input_file)
    
    initial_count = len(library.entries)
    console.print(f"[cyan]Found {initial_count} entries. Deduplicating...[/cyan]")
    
    deduped_library = BibDeduplicator.dedup(library)
    final_count = len(deduped_library.entries)
    
    duplicates_removed = initial_count - final_count
    
    BibParser.save(deduped_library, output_file)
    console.print(f"[bold green]Successfully saved deduplicated database to {output_file}[/bold green]")
    console.print(f"[yellow]Removed {duplicates_removed} duplicate entries.[/yellow]")

@app.command("resolve")
def resolve(
    input_file: Path = typer.Argument(..., help="Path to the input BibTeX file with messy entries"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Path to save the resolved file (defaults to overwrite)")
):
    """Resolve messy entries or missing DOIs by querying the Crossref API."""
    import asyncio
    
    if not output_file:
        output_file = input_file
        
    console.print(f"[cyan]Loading {input_file}...[/cyan]")
    library = BibParser.load(input_file)
    
    console.print(f"[cyan]Resolving {len(library.entries)} entries via Crossref API...[/cyan]")
    
    async def run_resolve():
        resolver = BibResolver()
        with console.status("[cyan]Querying Crossref API...") as status:
            def update_progress():
                pass # A simple callback
            await resolver.resolve_library(library, progress_callback=update_progress)
            
    asyncio.run(run_resolve())
    
    BibParser.save(library, output_file)
    console.print(f"[bold green]Successfully saved resolved database to {output_file}[/bold green]")

if __name__ == "__main__":
    app()
