# USAGE.md

## `kivi learn`

Aligns an ASR transcript with a ground-truth transcript, extracts mismatched entity pairs, computes phonetic keys, and updates memory weights.

* **Syntax:** `kivi learn --asr <text> --final <text> [--type <type_name>]...`
* **Example:** `kivi learn --asr "neo them" --final "Neovim" --type TECH_TERM`
* **Quirks & Edge Cases:**
* **Positional Mapping:** When multiple entities are extracted from a single sentence, `--type` flags map left-to-right.
* **Safe Evolution:** If fewer `--type` flags are provided than extracted entities, the missing ones default to `NULL`. The database uses `COALESCE` to preserve existing types if `NULL` is passed.
* **Excess Types:** Passing more `--type` flags than extracted entities triggers a CLI warning and ignores the excess.
* **Punctuation Immunity:** Identical tokens with different punctuation are ignored to prevent learning punctuation corrections.



## `kivi process`

Executes phonetic indexing, sliding-window n-gram retrieval, and LLM-guarded context disambiguation to correct misheard entities in formatting.

* **Syntax:** `kivi process --asr <text> --fmt <text>`
* **Example:** `kivi process --asr "open neo them" --fmt "Open neo them."`
* **Quirks & Edge Cases:**
* **Zero-Candidate Shortcut:** If the DB sliding window finds no phonetic matches, the command bypasses the LLM entirely, returning the exact `--fmt` string with near-zero latency.
* **Squashed Keys:** Automatically concatenates n-grams (e.g., "atom berg" -> "atomberg") to catch wrongly split compound entities.



## `kivi inspect`

Dumps known entities, their Double Metaphone keys, extracted TF-IDF context triggers, and confidence scores.

* **Syntax:** `kivi inspect [--entity <canonical_name>]`
* **Example:** `kivi inspect --entity "Neovim"`
* **Quirks & Edge Cases:**
* Omitting the `--entity` flag dumps the entire database.
* Results are strictly ordered by `confidence_score` (descending).



## `kivi forget`

Completely drops a learned entity from memory, instantly purging it from future retrieval.

* **Syntax:** `kivi forget --entity <canonical_name>`
* **Example:** `kivi forget --entity "Neovim"`
* **Quirks & Edge Cases:**
* **Case-Insensitive:** The `--entity` argument matches against the canonical form case-insensitively.
* **Cascading Deletion:** Relies on SQLite's `ON DELETE CASCADE`. Dropping the entity automatically wipes its associated `phonetic_aliases`, `memory_stats`, and `context_keywords`.
* **Global Stat Drift:** Deleting an entity removes its local context words, but it *does not* decrement the global word counts in `global_word_stats`. This is an architectural quirk that prioritizes speed over perfect global IDF recalculations when handling deletions.



## `kivi penalize`

Reduces the confidence score of an entity to gradually phase out false-positive LLM interventions without destroying the learned phonetic keys.

* **Syntax:** `kivi penalize --entity <canonical_name>`
* **Example:** `kivi penalize --entity "Neovim"`
* **Quirks & Edge Cases:**
* **Mathematical Decay:** Subtracts exactly `0.15` from the `confidence_score` per invocation. 
* **Zero-Floor Limit:** The confidence score is hard-floored at `0.0`. It will never drop into negative values, regardless of how many times it is penalized.
* **Rejection Logging:** Simultaneously increments the `rejected_interventions` counter in `memory_stats` to track historical inaccuracy.



## `kivi reset`

Wipes the SQLite database and reapplies the clean schema.

* **Syntax:** `kivi reset [--seed]`
* **Example:** `kivi reset --seed`
* **Quirks & Edge Cases:**
* **Hard Dependencies:** Will fail entirely if `src/db/schema.sql` is missing.
* **Seeding:** The `--seed` flag silently ignores the seed operation if `seeds/default.sql` is missing, but will still wipe the database.



## `kivi eval`

Executes the evaluation benchmark suite against a provided JSON dataset.

* **Syntax:** `kivi eval --dataset <path_to_json> --output <path_to_save>`
* **Example:** `kivi eval --dataset tests/bench.json --output results.json`
* **Quirks & Edge Cases:**
* Requires the input `--dataset` path to physically exist before running, otherwise Click will immediately throw a path validation error.

# RUN.md

For setup, environment variables, the primary review method, and the exact evaluation/reset commands, see the standalone [`RUN.md`](./RUN.md) in the repository root.
