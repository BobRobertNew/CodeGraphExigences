import hashlib
from thefuzz import process
from typing import List, Optional, Tuple

def generate_short_id(prefix: str, text: str, length: int = 8) -> str:
    """Generates a short unique ID based on a prefix and the MD5 hash of the text."""
    if not text:
        text = ""
    hash_object = hashlib.md5(text.encode('utf-8'))
    hash_hex = hash_object.hexdigest()
    return f"{prefix}-{hash_hex[:length].upper()}"

def find_best_match(query: str, choices: List[str], threshold: int = 70) -> Optional[str]:
    """Finds the best matching string from a list of choices using fuzzy matching."""
    if not choices or not query:
        return None

    result = process.extractOne(query, choices)
    if result:
        match, score = result[0], result[1]
        if score >= threshold:
            return match
    return None
