# src/engine/memory.py
from typing import List, Dict, Set
from src.engine.phonetics import get_phonetic_keys

def extract_ngrams(tokens: List[str], max_n: int = 3) -> List[str]:
    ngrams = []
    length = len(tokens)
    for n in range(1, max_n + 1):
        for i in range(length - n + 1):
            ngrams.append(" ".join(tokens[i:i+n]))
    return ngrams

def retrieve_candidates(asr: str, db) -> List[Dict]:
    tokens = asr.lower().split()
    ngrams = extract_ngrams(tokens, max_n=3)
    
    candidates = []
    seen_entity_ids: Set[str] = set()
    
    for ngram in ngrams:
        # 1. Standard Key: Preserves boundaries for standard multi-word entities
        std_pri, std_sec = get_phonetic_keys(ngram)
        matches = db.get_candidates(std_pri, std_sec)
        
        # 2. Squashed Key: Catches wrongly split compounds (e.g., "adam berg" -> "atomberg")
        squashed_ngram = ngram.replace(" ", "")
        if squashed_ngram != ngram:
            sq_pri, sq_sec = get_phonetic_keys(squashed_ngram)
            # Fetch and append additional matches if the squashed keys differ
            if (sq_pri, sq_sec) != (std_pri, std_sec):
                matches.extend(db.get_candidates(sq_pri, sq_sec))
        
        # Deduplicate and attach the matched n-gram metadata
        for match in matches:
            if match['id'] not in seen_entity_ids:
                seen_entity_ids.add(match['id'])
                match_copy = dict(match)
                match_copy['matched_ngram'] = ngram
                candidates.append(match_copy)
                
    return candidates
