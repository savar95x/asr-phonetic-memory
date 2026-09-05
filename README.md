# Kivi Phonetic Memory Layer

This text-to-text pipeline bridges the gap between raw Automatic Speech Recognition (ASR) hypotheses and final formatted text. It acts as a personalized phonetic memory system, learning a user’s unique vocabulary—names, companies, slang, and domain-specific terms—that standard models frequently transcribe phonetically but misspell.

The system builds this memory passively using `kivi learn` (by extracting context around corrections) and applies it dynamically using `kivi process` to correct future transcriptions with context-aware precision, entirely bypassing hardcoded dictionaries.

## Internal Architecture

### 1. The Learning Flow (`kivi learn`)

This flow processes ground-truth corrections to extract, encode, and memorize phonetic patterns.

* **Token Alignment:** The raw ASR text and corrected final text are lowercased and tokenized. A Sequence Matcher compares them to isolate exact substrings that were replaced (e.g., "adam berg" → "Atomberg").
* **Context Extraction:** For every replaced substring, a sliding window scans up to 4 words backward and forward. It hard-stops at syntactic boundaries (punctuation, conjunctions like "and", "but", "because") to ensure context remains highly localized. Stop words are stripped out.
* **Phonetic Encoding:** The canonical entity and its ASR alias are mapped to 4-character primary and secondary Double Metaphone keys.
* **Database Upsert & TF-IDF Update:**
    * The entity, its semantic `entity_type` (e.g., PERSON, TECH_TERM), and phonetic alias are saved.
    * Global document frequency is updated (how many total entities exist, and how many entities share this specific context word).
    * Local term frequency is incremented (how many times this specific entity appeared with this context word).
* **Confidence Calculation:** The observation count is incremented, and a continuous confidence score is recalculated using an asymptotic exponential curve, preventing single-mistake over-indexing.

### 2. The Processing Flow (`kivi process`)

This flow applies memory to live, raw ASR transcripts to resolve phonetic collisions.

* **N-Gram Generation:** Extracts 1-to-3 token sliding windows (n-grams) from the raw ASR string.
* **Key Computation & Squashing:** Each n-gram generates standard phonetic keys. Simultaneously, spaces are removed to create "squashed" keys (handling compound splits like "neo them" → "neovim"), calculating metaphones for both.
* **Vector Retrieval (Fast Path):** The SQLite database performs a live TF-IDF calculation filtering candidates based on context overlap. If no candidates clear the threshold (score $\ge 0.2$ and confidence $\ge 0.3$), the system bypasses the LLM entirely, yielding a 0ms latency return.
* **Context Guard (LLM Disambiguation):** If candidates match, the raw ASR, baseline formatted text, and retrieved phonetic candidates (including their `entity_type`) are passed to an LLM. Driven by strict spelling rules, cross-domain collision checks, and semantic type constraints (e.g., requiring grammatical syntax matches for `PERSON` or strict keyword matches for `TECH_TERM`), the guard decides whether to intervene, returning structured JSON with the corrected output and justification.

## Directory Structure

* **`src/cli.py`**: The central Click-based command-line interface. Wires commands (`learn`, `process`, `inspect`, `reset`, `eval`) to their respective engine functions.
* **`src/db/client.py`**: The SQLite database client. Handles WAL-mode connections, dynamic TF-IDF SQL queries, entity typing, and exponential confidence scoring.
* **`src/db/schema.sql`**: Table definitions isolating raw entities, global word frequencies, local contexts, and phonetic aliases.
* **`src/engine/aligner.py`**: Calculates textual diffs to find replaced words and extracts isolated, stop-word-filtered context bounds.
* **`src/engine/phonetics.py`**: Wraps the Double Metaphone implementation, normalizing phonetic hashes to optimal 4-character keys.
* **`src/engine/memory.py`**: Handles n-gram extraction, string squashing for compound words, and candidate retrieval from the database.
* **`src/engine/guard.py`**: Interfaces with the OpenAI-compatible LLM, supplying system prompts, semantic type rules, and candidate payloads to safely resolve ambiguous phonetic matches.
* **`eval/runner.py`**: Multi-threaded evaluation suite that benchmarks true positives, false positives, and latency metrics across an evaluation dataset.

## Algorithms Used

* **Double Metaphone (Phonetics):** Replaces older algorithms like Soundex. It accounts for irregularities in English and non-English spelling/pronunciation by returning both a primary and a secondary phonetic code (e.g., treating "J" and "Y" similarly in Germanic names). Chosen because it strictly minimizes false negatives during phonetic lookups.
* **Gestalt Pattern Matching (`difflib.SequenceMatcher`):** Used during the learning phase to align ASR with Final text. Chosen over Levenshtein distance because it excels at finding the longest contiguous matching subsequences, smoothly handling structural insertions/deletions (like dropped words in ASR) rather than just character-level edits.
* **Smoothed TF-IDF (Context Weighting):** Calculates term relevance strictly within SQL.
    * *Formula:* `local_frequency * log((total_entities + 2.0) / (entity_count + 1.0))`
    * *Why:* A simple frequency count fails because common words drown out strong contextual signals. TF-IDF ensures that unique, domain-specific surrounding words highly boost a candidate, while generic words are mathematically neutralized.
* **Asymptotic Exponential Decay (Confidence Scoring):**
    * *Formula:* $1.0 - (1.0 - 0.7) \cdot e^{-0.3 \cdot (observations - 1)}$
    * *Why:* Ensures the system doesn't instantly trust an entity seen only once (starting at a base $0.70$ confidence), but rapidly builds trust toward $1.0$ as the entity is observed multiple times across different contexts.

## Database Schema

* `entities`: Stores the core `canonical_form` of the learned word, its semantic `entity_type` for disambiguation routing, alongside its computed primary and secondary metaphones. This is the root table for foreign keys.
* `system_stats`: A singleton row tracking `total_entities`. Used dynamically in the `kivi process` SQL query as the numerator for the Inverse Document Frequency (IDF) calculation.
* `global_word_stats`: Tracks the global frequency of context words across all entities. Serves as the `entity_count` denominator in the IDF calculation. If a word is attached to many different entities (e.g., "the", "said"), its IDF approaches zero.
* `phonetic_aliases`: Captures the actual ASR mistakes (the `alias`) that led to a correction. Maps back to `entity_id`. Useful for direct matching and bypassing fuzzy phonetic logic when a known, exact mistake recurs.
* `context_keywords`: The many-to-many bridge linking an `entity_id` to a `keyword`. Stores the `local_frequency` (Term Frequency), which is how many times this specific entity was spoken near this specific word.
* `memory_stats`: Tracks `observations_count` and the resulting `confidence_score`. Evaluated at runtime to filter out highly speculative candidates before sending them to the LLM guard.

## Decisions & Challenges

* **In-Database Math over Python Processing:** Calculating TF-IDF in Python would require dumping massive amounts of keyword data into memory on every request. By injecting `math.log` into the SQLite connection, candidate filtering is executed entirely within the C-optimized SQL engine, resulting in microsecond retrieval times.
* **Challenge: Compound Word Splitting:** A major hurdle was ASR models erroneously inserting spaces into single entities (e.g., transcribing "Atomberg" as "Adam Berg"). Standard n-gram phonetic matching fails because "Adam" and "Berg" evaluate to separate phonetic keys. This was solved by the "Squashed Key" algorithm in `memory.py`, which strips spaces from the 2- and 3-grams before phonetic encoding, ensuring "Adam Berg" hits the exact same phonetic index as "Atomberg".
* **Challenge: LLM Over-Correction:** Initial iterations resulted in the LLM replacing valid English words with similar-sounding entities when context was weak. Solved by defining strict cross-domain collision rules in `guard.py`, introducing `entity_type` logic for strict semantic parsing, and strictly requiring the LLM to return `output` and `interventions` JSON keys to force chain-of-thought justification before replacement.

## Limitations & AI Use

* **Latency:** While zero-candidate queries safely bypass the LLM for immediate processing (0ms overhead), ambiguous phonetic matches require an external API call, introducing network latency governed by the upstream LLM provider.
* **Collisions:** If two identical phonetic entities (e.g., "Stephen" and "Steven") share highly similar global word statistics, the system relies heavily on the LLM's default spelling rules, which may occasionally result in false positives.
* **Benchmark Performance:** In the seed+dataset given, my results come out to be `[INSERT ACCURACY]%` true-positive intervention accuracy, with a false positive rate of `[INSERT FPR]%`, while taking `[INSERT LATENCY]ms` p50 latency with the `[INSERT MODEL NAME]` model (free dev testing tier).
