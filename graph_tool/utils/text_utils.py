import hashlib
from rapidfuzz import process
from typing import List, Optional, Tuple

def generate_short_id(prefix: str, text: str, length: int = 8) -> str:
    """
    Generates a short unique ID based on a prefix and the SHA-256 hash of the text.

    Args:
        prefix (str): The prefix to prepend to the ID.
        text (str): The string to hash.
        length (int): The number of characters from the hash to include. Defaults to 8.

    Returns:
        str: The generated short ID.
    """
    if not text:
        text = ""
    hash_object = hashlib.sha256(text.encode('utf-8'))
    hash_hex = hash_object.hexdigest()
    return f"{prefix}-{hash_hex[:length].upper()}"

def find_best_match(query: str, choices: List[str], threshold: int = 70) -> Optional[str]:
    """
    Finds the best matching string from a list of choices using fuzzy matching.

    Args:
        query (str): The target string to match.
        choices (List[str]): A list of candidate strings.
        threshold (int): The minimum fuzzy match score (0-100) to accept a match. Defaults to 70.

    Returns:
        Optional[str]: The best matching string if its score meets the threshold, otherwise None.
    """
    if not choices or not query:
        return None

    result = process.extractOne(query, choices)
    if result:
        match, score = result[0], result[1]
        if score >= threshold:
            return match
    return None
