# src/engine/phonetics.py
from doublemetaphone import doublemetaphone

def get_phonetic_keys(word: str) -> tuple[str, str]:
    """Returns the full, untruncated (primary, secondary) Double Metaphone keys."""
    primary, secondary = doublemetaphone(word)
    pri = primary or ""
    sec = secondary or primary or ""
    return pri, sec
