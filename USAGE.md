# USAGE.md

Per-command reference for the `kivi` CLI. For setup, env vars, evaluation, and resetting, see [`RUN.md`](./RUN.md).

## `kivi learn`

Aligns an ASR transcript with a ground-truth transcript, extracts mismatched entity pairs, computes phonetic keys, and updates memory weights.

* **Syntax:** `kivi learn --asr <text> --final <text> [--type <type_name>]...`
* **Example:** `kivi learn --asr "neo them" --final "Neovim" --type TECH_TERM`
* **Output:** JSON `{"learned": [ {canonical, alias, entity_type, primary_metaphone, secondary_metaphone, extracted_context, updated_context_weights, confidence_score} ]}`. An empty `learned` array means nothing worth learning was found (e.g. a punctuation-only correction).
* **Edge cases:**
  * `--type` flags map left-to-right to extracted entities; extras trigger a warning, missing ones default to `NULL` (the DB preserves existing types via `COALESCE`).
  * Re-learning merges idempotently (deterministic `id` = `lower(canonical).replace(" ","_")`) — observations and confidence increase, existing aliases are kept.
  * Tokens are punctuation-stripped before diffing, so punctuation-only corrections (including trailing full-stops) are never learned.

## `kivi process`

Resolves misheard entities in formatted text using memory.

* **Syntax:** `kivi process --asr <text> --fmt <text>`
* **Example:** `kivi process --asr "open neo them" --fmt "Open neo them."`
* **Output:** JSON `{asr, formatted, memory_aware, interventions: [{original, replacement, matched_context, confidence, reason}], latency_ms}`. On the fast path, `memory_aware == formatted` and `interventions` is empty.
* **Edge cases:**
  * No phonetic matches → LLM bypassed entirely; returns `--fmt` unchanged at near-zero latency.
  * N-grams are both standard and "squashed" (e.g. `atom berg` → `atomberg`), so split compounds are caught while multi-word entities stay intact.
  * Guard runs deterministic: `temperature=0.0`, strict JSON mode, `MAX_RETRIES` retries (default 2, env `MAX_RETRIES`).

## `kivi inspect`

Dumps known entities, phonetic keys, TF-IDF context triggers, and confidence scores.

* **Syntax:** `kivi inspect [--entity <canonical_name>]`
* **Example:** `kivi inspect --entity "Neovim"`
* **Output:** JSON array of `{canonical_form, entity_type, primary_metaphone, secondary_metaphone, aliases, context_weights (sorted desc), confidence_score, observations}` — `[]` if the entity doesn't exist.
* **Edge cases:** Omitting `--entity` dumps the entire database. Results ordered by `confidence_score` descending.

## `kivi forget`

Hard-deletes a learned entity from memory.

* **Syntax:** `kivi forget --entity <canonical_name>`
* **Example:** `kivi forget --entity "Neovim"`
* **Output:** `Entity '<X>' forgotten successfully.` (green) on success, `Warning: Entity '<X>' not found in database.` (red, stderr) otherwise. Exit code `0` either way.
* **Edge cases:**
  * Matching is case-insensitive.
  * `ON DELETE CASCADE` wipes the entity's `phonetic_aliases`, `memory_stats`, and `context_keywords`.
  * Global counts in `global_word_stats` are *not* decremented — intentional, prioritizing speed over perfect IDF recomputation on deletion.

## `kivi penalize`

Soft-decays an entity that the LLM over-applies, without destroying its learned phonetic data.

* **Syntax:** `kivi penalize --entity <canonical_name>`
* **Example:** `kivi penalize --entity "Neovim"`
* **Output:** `Entity '<X>' penalized. Confidence score has been reduced.` (yellow) on success, or the standard not-found warning (red, stderr). Exit code `0` either way.
* **Edge cases:**
  * Subtracts exactly `0.15` from `confidence_score` per call, hard-floored at `0.0`.
  * Increments `rejected_interventions` to track historical inaccuracy.

## `kivi reset`

Wipes the SQLite database and reapplies the clean schema.

* **Syntax:** `kivi reset [--seed]`
* **Example:** `kivi reset --seed`
* **Output:** `Database reset and seeded successfully.` (green) with `--seed`; `Database wiped and clean schema applied.` (yellow) otherwise.
* **Edge cases:**
  * Fails entirely if `src/db/schema.sql` is missing.
  * With `--seed`, a missing `seeds/default.sql` is silently ignored — the database is still wiped.

## `kivi eval`

Runs the evaluation benchmark against a JSON dataset.

* **Syntax:** `kivi eval --dataset <path_to_json> --output <path_to_save>`
* **Example:** `kivi eval --dataset eval/dataset.json --output eval/results.json`
* **Output:** Writes `{summary, traces}` (aggregate metrics + per-case audit) to `--output`, prints `Evaluation finished. Metrics written to <output>`.
* **Edge cases:**
  * `--dataset` must physically exist; Click validates the path.
  * Worker count via `MAX_WORKERS` env var (default `20`; lower to `7` for free/rate-limited keys). The committed `eval/results.json` was generated at 7 workers.
