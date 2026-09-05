# src/engine/aligner.py
import difflib
import string
from typing import List, Dict

# Comprehensive English stop-word list to eliminate noise
STOP_WORDS = {
    # Pronouns & determiners
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", 
    "theirs", "themselves", "what", "which", "who", "whom", "whose", "this", 
    "that", "these", "those", "all", "another", "any", "anybody", "anyone", 
    "anything", "both", "each", "either", "every", "everybody", "everyone", 
    "everything", "few", "many", "neither", "nobody", "none", "noone", 
    "nothing", "one", "other", "others", "several", "some", "somebody", 
    "someone", "something", "such",

    # Articles & prepositions
    "a", "an", "the", "about", "above", "across", "after", "afterwards", 
    "against", "along", "alongside", "amid", "among", "amongst", "around", 
    "as", "at", "before", "behind", "below", "beneath", "beside", "besides", 
    "between", "beyond", "by", "concerning", "despite", "down", "during", 
    "except", "for", "from", "in", "inside", "into", "near", "of", "off", 
    "on", "onto", "out", "outside", "over", "past", "per", "regarding", 
    "round", "since", "through", "throughout", "till", "to", "toward", 
    "towards", "under", "underneath", "until", "unto", "up", "upon", 
    "via", "with", "within", "without",

    # Conjunctions & transitions
    "and", "but", "if", "or", "because", "while", "though", "although", 
    "even", "unless", "whereas", "wherever", "whenever", "whether", "so", 
    "then", "thus", "hence", "therefore", "however", "furthermore", "moreover",

    # Auxiliary & modal verbs (and common forms)
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", 
    "had", "having", "do", "does", "did", "doing", "done", "can", "could", 
    "may", "might", "must", "shall", "should", "will", "would", "dare", 
    "ought", "need", "used", "get", "gets", "got", "getting", "gotten", 
    "go", "goes", "going", "went", "gone",

    # Negations & isolated contraction fragments
    "no", "nor", "not", "cannot", "n't", "nt", "don", "dont", "doesnt", 
    "didnt", "isnt", "arent", "wasnt", "werent", "havent", "hasnt", "hadnt", 
    "wont", "wouldnt", "cant", "couldnt", "shouldnt", "mustnt",
    "s", "t", "d", "m", "re", "ve", "ll",

    # Adverbs, qualifiers & degree words
    "again", "almost", "already", "also", "always", "anyway", "anywhere", 
    "back", "else", "elsewhere", "enough", "ever", "everywhere", "far", 
    "further", "here", "hereafter", "hereby", "herein", "hereupon", "how", 
    "however", "indeed", "just", "less", "least", "more", "most", "mostly", 
    "much", "never", "nevertheless", "next", "no", "now", "nowhere", "often", 
    "only", "quite", "rather", "seldom", "somehow", "somewhere", "soon", 
    "still", "than", "there", "thereafter", "thereby", "therefore", "therein", 
    "thereupon", "too", "very", "when", "where", "whereby", "wherein", 
    "whereupon", "why", "yet",

    # Conversational speech fillers, hedges & discourse markers
    "actually", "basically", "literally", "seriously", "honestly", "frankly", 
    "definitely", "certainly", "probably", "maybe", "perhaps", "supposedly", 
    "essentially", "virtually", "simply", "totally", "completely", "really", 
    "pretty", "yeah", "yes", "yep", "nah", "nope", "okay", "ok", "hey", 
    #"mean", "please", "alright", "sort", "kind",
    "hello", "hi", "uh", "um", "ah", "er", "like", "well", "right", "sure" 
}

def extract_learning_pairs(asr: str, final: str, window: int = 4) -> List[Dict]:
    """Finds replaced words between ASR and Final, stopping at soft syntactic boundaries."""
    # Strip punctuation from each token so SequenceMatcher compares raw words
    asr_tokens = [t.strip(string.punctuation) for t in asr.lower().split()]
    final_tokens = [t.strip(string.punctuation) for t in final.split()]
    
    matcher = difflib.SequenceMatcher(None, [t.lower() for t in asr_tokens], [t.lower() for t in final_tokens])
    pairs = []
    
    # Define words and punctuation that hard-stop context collection
    BOUNDARIES = {"and", "but", "or", ".", ",", ";", "?", "!",
                  "because", "so", "then", "which", "however", "therefore", "although", "since", "unless"}
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            alias = " ".join(asr_tokens[i1:i2]).strip(string.punctuation)
            canonical = " ".join(final_tokens[j1:j2]).strip(string.punctuation)
            
            # Skip identical words to prevent learning punctuation corrections
            if not alias or not canonical or alias.lower() == canonical.lower():
                continue
            
            context = []
            
            # Look backwards up to 'window' tokens
            for idx in range(i1 - 1, max(-1, i1 - window - 1), -1):
                word = asr_tokens[idx].lower()
                if word in BOUNDARIES or any(char in BOUNDARIES for char in word):
                    break
                context.append(word)
                
            # Look forwards up to 'window' tokens
            for idx in range(i2, min(len(asr_tokens), i2 + window)):
                word = asr_tokens[idx].lower()
                if word in BOUNDARIES or any(char in BOUNDARIES for char in word):
                    break
                context.append(word)

            # Strip punctuation, filter against STOP_WORDS, and prevent the alias itself from becoming a context keyword
            exclude_set = STOP_WORDS.union(set(alias.lower().split()))
            clean_context = [
                t.strip(string.punctuation) for t in context 
                if t.strip(string.punctuation) not in exclude_set 
                and t.strip(string.punctuation)
            ]
            
            pairs.append({
                "alias": alias,
                "canonical": canonical,
                "context": list(set(clean_context))
            })
            
    return pairs
