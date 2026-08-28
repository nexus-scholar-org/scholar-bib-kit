import asyncio
from urllib.parse import quote_plus
import bibtexparser
from bibtexparser.library import Library
from bibtexparser.model import Entry
from scholar_search.http_client import AcademicHttpClient

class BibResolver:
    def __init__(self):
        # Crossref polite pool rate limit is typically around 50 requests/second,
        # but we'll be conservative with 10.
        self.http_client = AcademicHttpClient(name="crossref-resolver", rate_limit=10)
        
    async def resolve_doi(self, doi: str) -> str | None:
        """Fetch BibTeX string directly from Crossref using a DOI."""
        url = f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
        try:
            response = await self.http_client.get(url=url)
            print(f"DOI {doi} status: {response.status_code}, content: {response.text[:100]}")
            if response.status_code == 200 and response.text.strip():
                return response.text
        except Exception as e:
            print(f"Error fetching DOI {doi}: {e}")
            pass
        return None
        
    async def resolve_search(self, title: str, author: str = "") -> str | None:
        """Search Crossref by title/author to find a DOI, then fetch BibTeX."""
        query = quote_plus(f"{title} {author}".strip())
        url = f"https://api.crossref.org/works?query.bibliographic={query}&rows=1"
        try:
            response = await self.http_client.get(url=url)
            print(f"Search status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                items = data.get("message", {}).get("items", [])
                if items and len(items) > 0:
                    doi = items[0].get("DOI")
                    print(f"Found DOI from search: {doi}")
                    if doi:
                        # Once we have the DOI, fetch the exact BibTeX
                        return await self.resolve_doi(doi)
        except Exception:
            pass
        return None

    async def resolve_entry(self, entry: Entry) -> None:
        """Attempt to resolve a single entry and update it in-place."""
        print(f"Resolving entry: {entry.key}")
        doi_field = entry.fields_dict.get("doi")
        title_field = entry.fields_dict.get("title")
        author_field = entry.fields_dict.get("author")
        
        print(f"DOI field: {doi_field}")
        bibtex_str = None
        
        if doi_field and doi_field.value:
            # Clean DOI just in case it has URL prefixes
            doi = doi_field.value.replace("https://doi.org/", "").replace("http://doi.org/", "")
            print(f"Using DOI: {doi}")
            bibtex_str = await self.resolve_doi(doi)
            
        if not bibtex_str and title_field and title_field.value:
            # Fallback to search
            title = title_field.value
            author = author_field.value if author_field else ""
            bibtex_str = await self.resolve_search(title, author)
            
        if bibtex_str:
            # Parse the returned string into a temporary library
            try:
                temp_lib = bibtexparser.parse_string(bibtex_str)
                if temp_lib.entries:
                    new_entry = temp_lib.entries[0]
                    print(f"Resolved new entry for {entry.key} with {len(new_entry.fields_dict)} fields")
                    # Restore original key
                    original_key = entry.key
                    new_entry.key = original_key
                    # Update fields
                    entry.fields_dict.clear()
                    entry.entry_type = new_entry.entry_type
                    for key, field in new_entry.fields_dict.items():
                        entry.set_field(field)
                else:
                    print(f"No entries parsed from crossref string for {entry.key}: {bibtex_str}")
            except Exception as e:
                print(f"Exception parsing bibtex string: {e}")

    async def resolve_library(self, library: Library, progress_callback=None) -> Library:
        """Resolve all entries in a library."""
        tasks = []
        for entry in library.entries:
            tasks.append(self.resolve_entry(entry))
            
        for coro in asyncio.as_completed(tasks):
            await coro
            if progress_callback:
                progress_callback()
                
        return library
