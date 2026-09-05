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

```markdown
## Primary Review Method
Local command-line interface (written in python) connected to an embedded local database (SQLite).

## Setup & Execution

* Create a dedicated virtual environment in the project root: `python3 -m venv venv`
* Activate the virtual environment: `source venv/bin/activate`
* Install the package and its dependencies in editable mode: `pip install -e .`
* Create a `.env` file in the root directory containing your `API_KEY`, `API_BASE`, and `MODEL` parameters (see `.env.example`).
* Wipe the existing state and apply the clean SQLite schema: `kivi reset --seed`
* Train the system on a new phonetic entity by providing the ASR, ground-truth text, and entity type: `kivi learn --asr "ask aditya" --final "Ask Aaditya" --type PERSON`
* Process a live transcription to see the memory-aware output: `kivi process --asr "ask aditya" --fmt "Ask Aditya."`

## Evaluation & Inspection

* Inspect the internal database state, confidence scores, and dynamic context weights for any learned word: `kivi inspect --entity aaditya`
* Execute the full evaluation suite against a target JSON dataset to generate latency and accuracy metrics: `kivi eval --dataset path/to/dataset.json --output eval_metrics.json`

For any help anywhere in the process, just do `kivi --help`

## Features & Usage

Kivi operates entirely through a command-line interface, providing seven core commands to manage and evaluate your phonetic memory layer:

### 1. Learning New Vocabulary (`kivi learn`)
Extracts entities and contextual triggers from a corrected transcription and saves them to the database. You can specify semantic types to improve disambiguation accuracy.
```bash
kivi learn --asr "deploy to the neo them container" --final "deploy to the Neovim container" --type TECH_TERM


```

*Outputs:* A JSON block showing the updated context weights, extracted aliases, phonetic keys, and recalculated confidence scores.

### 2. Processing Live Transcriptions (`kivi process`)

Takes a raw ASR hypothesis and its baseline formatted text, retrieves matching candidates using local/global context scores, and passes them through an LLM context guard to resolve phonetic collisions safely.

```bash
kivi process --asr "tell atom berg to cache it in read is" --fmt "Tell Adam Berg to cache it in read is."


```

*Outputs:* A JSON response containing the `memory_aware` (corrected) string, latency, and a detailed `interventions` array justifying any changes made by the guard.

### 3. Inspecting Memory (`kivi inspect`)

Dumps the current state of an entity (or all entities), including its associated context triggers, calculated TF-IDF weights, observation counts, and confidence scores.

```bash
kivi inspect --entity "Redis"


```

### 4. Forgetting Entities (`kivi forget`)

Completely removes an incorrectly learned entity from the memory layer. This executes a cascading deletion, wiping out the canonical entity, its phonetic aliases, and all contextual word frequencies.

```bash
kivi forget --entity "Neovim"


```

### 5. Penalizing Interventions (`kivi penalize`)

Soft-decays an entity that the LLM applies too aggressively. Decreases the confidence score by 0.15 (floored at 0.0) and increments the rejection counter, safely suppressing the entity without erasing its learned context vectors.

```bash
kivi penalize --entity "Neovim"


```

### 6. Database Management (`kivi reset`)

Wipes the local SQLite database and reapplies the base schema. Essential for starting fresh or applying schema migrations.

```bash
kivi reset --seed


```

*(The `--seed` flag safely populates the database with default entities and global stats for immediate testing).*

### 7. Running Evaluations (`kivi eval`)

Executes the evaluation runner over an entire benchmark dataset to calculate precision, recall, false positive rates, and latency profiles.

```bash
kivi eval --dataset tests/eval_data.json --output results.json


```

> [Note]
> For more usage, check out [USAGE.md](https://www.google.com/search?q=USAGE.md)

```

```
