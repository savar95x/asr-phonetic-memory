# src/engine/phonetics.py
from doublemetaphone import doublemetaphone

def get_phonetic_keys(word: str) -> tuple[str, str]:
    """Returns (primary, secondary) Double Metaphone keys, normalized to 4 chars."""
    primary, secondary = doublemetaphone(word)
    pri = (primary or "")[:4]
    sec = (secondary or primary or "")[:4]
    return pri, sec
