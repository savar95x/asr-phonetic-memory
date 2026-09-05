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
