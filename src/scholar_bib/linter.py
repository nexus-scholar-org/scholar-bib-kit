import re
from bibtexparser.library import Library

class BibLinter:
    @staticmethod
    def lint(library: Library, generate_keys: bool = False) -> Library:
        """Lint a BibTeX library: wrap titles in braces to preserve case, normalize keys."""
        existing_keys = set()
        
        for entry in library.entries:
            # 1. Wrap title in double braces
            title_field = entry.fields_dict.get('title')
            if title_field and isinstance(title_field.value, str):
                title = title_field.value
                # If the title is not already wrapped in braces (which v2 might have stripped)
                # we add braces to ensure case preservation
                if not (title.startswith('{') and title.endswith('}')):
                    title_field.value = f"{{{title}}}"
            
            # 2. Key Generation
            if generate_keys:
                author_field = entry.fields_dict.get('author')
                year_field = entry.fields_dict.get('year')
                
                if author_field and year_field and isinstance(author_field.value, str):
                    # Extract the first author's last name
                    first_author_full = author_field.value.split(' and ')[0]
                    # Handle "LastName, FirstName" or "FirstName LastName"
                    if ',' in first_author_full:
                        first_author = first_author_full.split(',')[0].strip()
                    else:
                        first_author = first_author_full.split(' ')[-1].strip()
                        
                    first_author = re.sub(r'[^a-zA-Z]', '', first_author)
                    year = re.sub(r'[^0-9]', '', str(year_field.value))
                    
                    if first_author and year:
                        base_key = f"{first_author}{year}"
                        new_key = base_key
                        suffix = 97 # 'a'
                        
                        while new_key in existing_keys and new_key != entry.key:
                            new_key = f"{base_key}{chr(suffix)}"
                            suffix += 1
                            
                        entry.key = new_key
            
            existing_keys.add(entry.key)
            
        return library
