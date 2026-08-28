import re
from bibtexparser.library import Library
from bibtexparser.model import Entry

def _clean_string(s: str) -> str:
    """Clean a string for comparison."""
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

class BibDeduplicator:
    @staticmethod
    def dedup(library: Library) -> Library:
        """Remove duplicates from a BibTeX library based on DOI and Title."""
        unique_entries: list[Entry] = []
        
        doi_map = {}
        title_map = {}
        
        for entry in library.entries:
            is_duplicate = False
            target_idx = -1
            
            doi_field = entry.fields_dict.get('doi')
            doi_val = _clean_string(doi_field.value) if doi_field else None
            
            title_field = entry.fields_dict.get('title')
            title_val = _clean_string(title_field.value) if title_field else None
            
            if doi_val and doi_val in doi_map:
                is_duplicate = True
                target_idx = doi_map[doi_val]
            elif title_val and title_val in title_map:
                is_duplicate = True
                target_idx = title_map[title_val]
                
            if is_duplicate:
                # Merge missing fields into the existing entry
                target_entry = unique_entries[target_idx]
                for key, field in entry.fields_dict.items():
                    if key not in target_entry.fields_dict:
                        target_entry.set_field(field)
            else:
                # Add as new unique entry
                idx = len(unique_entries)
                unique_entries.append(entry)
                if doi_val:
                    doi_map[doi_val] = idx
                if title_val:
                    title_map[title_val] = idx
                    
        # Replace entries in the library with the deduplicated ones
        # We create a new Library to safely hold the clean entries
        new_lib = Library()
        # Ensure we keep blocks like comments or preamble
        for block in library.blocks:
            if not isinstance(block, Entry):
                new_lib.add(block)
        for entry in unique_entries:
            new_lib.add(entry)
            
        return new_lib
