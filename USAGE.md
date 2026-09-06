# USAGE.md

## `kivi learn`

Aligns an ASR transcript with a ground-truth transcript, extracts mismatched entity pairs, computes phonetic keys, and updates memory weights.

* **Syntax:** `kivi learn --asr <text> --final <text> [--type <type_name>]...`
* **Example:** `kivi learn --asr "neo them" --final "Neovim" --type TECH_TERM`
* **Output:** JSON `{"learned": [ {canonical, alias, entity_type, primary_metaphone, secondary_metaphone, extracted_context, updated_context_weights, confidence_score} ]}`. An empty `learned` array means nothing worth learning was found (e.g. a correction that only touched punctuation).
* **Quirks & Edge Cases:**
* **Positional Mapping:** When multiple entities are extracted from a single sentence, `--type` flags map left-to-right.
* **Safe Evolution:** If fewer `--type` flags are provided than extracted entities, the missing ones default to `NULL`. The database uses `COALESCE` to preserve existing types if `NULL` is passed.
* **Excess Types:** Passing more `--type` flags than extracted entities triggers a CLI warning and ignores the excess.
* **Idempotent Merge:** Re-learning a correction that already exists **merges** with the stored entity (deterministic `id` = `lower(canonical).replace(" ","_")`) — it never duplicates. `observations_count` and confidence increase, existing aliases are left alone, and per-keyword `local_frequency` is bumped. See README → "How `kivi learn` confidently finds an already-known entity".
* **Punctuation Immunity:** Every token is punctuation-stripped *before* diffing, so `"Kubernetes."` vs `"Kubernetes"` diff as equal — punctuation-only corrections (including a trailing full-stop on the final word) are never learned.



## `kivi process`

Executes phonetic indexing, sliding-window n-gram retrieval, and LLM-guarded context disambiguation to correct misheard entities in formatting.

* **Syntax:** `kivi process --asr <text> --fmt <text>`
* **Example:** `kivi process --asr "open neo them" --fmt "Open neo them."`
* **Output:** JSON `{asr, formatted, memory_aware, interventions: [{original, replacement, matched_context, confidence, reason}], latency_ms}`. On the fast path `memory_aware == formatted` and `interventions` is empty.
* **Quirks & Edge Cases:**
* **Zero-Candidate Shortcut:** If the DB sliding window finds no phonetic matches, the command bypasses the LLM entirely, returning the exact `--fmt` string with near-zero latency.
* **Squashed Keys:** Automatically concatenates n-grams (e.g., "atom berg" -> "atomberg") to catch wrongly split compound entities — while still matching the *standard* (space-preserving) key so intended multi-word entities like "Max Payne" are never collapsed.
* **Deterministic Guard:** When the LLM guard runs, it uses `temperature=0.0`, strict JSON mode, and `MAX_RETRIES` retries (default 2, env `MAX_RETRIES`) so identical inputs produce stable output.



## `kivi inspect`

Dumps known entities, their Double Metaphone keys, extracted TF-IDF context triggers, and confidence scores.

* **Syntax:** `kivi inspect [--entity <canonical_name>]`
* **Example:** `kivi inspect --entity "Neovim"`
* **Output:** JSON array of `{canonical_form, entity_type, primary_metaphone, secondary_metaphone, aliases, context_weights (dict sorted desc), confidence_score, observations}` — `[]` if `--entity` doesn't exist.
* **Quirks & Edge Cases:**
* Omitting the `--entity` flag dumps the entire database.
* Results are strictly ordered by `confidence_score` (descending).



## `kivi forget`

Completely drops a learned entity from memory, instantly purging it from future retrieval.

* **Syntax:** `kivi forget --entity <canonical_name>`
* **Example:** `kivi forget --entity "Neovim"`
* **Output:** Prints `Entity '<X>' forgotten successfully.` (green) on success, or `Warning: Entity '<X>' not found in database.` (red, to stderr) otherwise. Note the process exits with code `0` either way — check the message, not the exit code.
* **Quirks & Edge Cases:**
* **Case-Insensitive:** The `--entity` argument matches against the canonical form case-insensitively.
* **Cascading Deletion:** Relies on SQLite's `ON DELETE CASCADE`. Dropping the entity automatically wipes its associated `phonetic_aliases`, `memory_stats`, and `context_keywords`.
* **Global Stat Drift:** Deleting an entity removes its local context words, but it *does not* decrement the global word counts in `global_word_stats`. This is an architectural quirk that prioritizes speed over perfect global IDF recalculations when handling deletions.



## `kivi penalize`

Reduces the confidence score of an entity to gradually phase out false-positive LLM interventions without destroying the learned phonetic keys.

* **Syntax:** `kivi penalize --entity <canonical_name>`
* **Example:** `kivi penalize --entity "Neovim"`
* **Output:** Prints `Entity '<X>' penalized. Confidence score has been reduced.` (yellow) on success, or the same `Warning: Entity '<X>' not found in database.` (red, to stderr) otherwise. Exit code is `0` either way.
* **Quirks & Edge Cases:**
* **Mathematical Decay:** Subtracts exactly `0.15` from the `confidence_score` per invocation. 
* **Zero-Floor Limit:** The confidence score is hard-floored at `0.0`. It will never drop into negative values, regardless of how many times it is penalized.
* **Rejection Logging:** Simultaneously increments the `rejected_interventions` counter in `memory_stats` to track historical inaccuracy.



## `kivi reset`

Wipes the SQLite database and reapplies the clean schema.

* **Syntax:** `kivi reset [--seed]`
* **Example:** `kivi reset --seed`
* **Output:** Prints `Database reset and seeded successfully.` (green) with `--seed` and a valid seed file; otherwise `Database wiped and clean schema applied.` (yellow); `Error: src/db/schema.sql not found.` (red) if the schema is missing.
* **Quirks & Edge Cases:**
* **Hard Dependencies:** Will fail entirely if `src/db/schema.sql` is missing.
* **Seeding:** The `--seed` flag silently ignores the seed operation if `seeds/default.sql` is missing, but will still wipe the database.



## `kivi eval`

Executes the evaluation benchmark suite against a provided JSON dataset.

* **Syntax:** `kivi eval --dataset <path_to_json> --output <path_to_save>`
* **Example:** `kivi eval --dataset eval/dataset.json --output eval/results.json`
* **Output:** Writes `{summary, traces}` (full per-case audit + aggregate metrics) to the `--output` file and prints `Evaluation finished. Metrics written to <output>`.
* **Quirks & Edge Cases:**
* Requires the input `--dataset` path to physically exist before running, otherwise Click will immediately throw a path validation error.
* Worker count is configurable via the `MAX_WORKERS` env var (default `20`; lower to `7` if your API key is rate-limited, e.g. free tier). The committed `eval/results.json` was generated at 7 workers.

# RUN.md

For setup, environment variables, the primary review method, and the exact evaluation/reset commands, see the standalone [`RUN.md`](./RUN.md) in the repository root.
