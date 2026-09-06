# RUN.md

## Primary Review Method

**Local command-line interface (Python) connected to an embedded local database (SQLite).** Nothing is hosted, no browser interface, no server to keep running. The whole journey — learning, inspecting, processing, resetting, and evaluating — happens through `kivi` commands in a terminal.

## Prerequisites (Runtimes & Versions)

* **Python 3.10+** (developed on CPython 3.14; any 3.10+ interpreter works).
* An **OpenAI-compatible API key** for the context-guard LLM (any provider exposing a `/v1/chat/completions` endpoint; the repo defaults to the DashScope Alibaba Cloud compatible-mode endpoint).
* `git` (only to clone the repository).

## Environment Variables

Create a `.env` file in the project root. A ready-made template is committed at `.env.example` (copy it and fill in your key). `API_BASE`, `API_KEY`, and `MODEL` are **required** and are read directly by `src/engine/guard.py`; `MAX_WORKERS` and `MAX_RETRIES` are **optional** and have sensible defaults:

| Variable       | Description                                                             | Default |
| -------------- | ----------------------------------------------------------------------- | ------- |
| `API_BASE`     | Base URL of the OpenAI-compatible chat completions endpoint.             | —       |
| `API_KEY`      | Your secret API key. Never commit the real value — `.env` is gitignored. | —       |
| `MODEL`        | Model id used by the guard (e.g. `qwen3.6-plus`, `qwen3.6-flash`).       | —       |
| `MAX_WORKERS`  | Concurrent worker threads for `kivi eval` (`eval/runner.py`). Lower to `7` if rate-limited on a free key. | `20` |
| `MAX_RETRIES`  | Automatic retries per LLM API request (`src/engine/guard.py`).          | `2`     |

## Setup & Installation

```bash
git clone <repo-url>
cd <repo>
python3 -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env     # then put your real API_KEY inside .env
```

## Database Creation, Migration & Seeding

SQLite "migrations" are idempotent DDL: `kivi reset` drops and reapplies `src/db/schema.sql`. Seeding loads the deterministic baseline memory from `seeds/default.sql`.

```bash
# Creates .kivi/memory.db, applies schema.sql, and loads seeds/default.sql (50 entities)
kivi reset --seed

# Or schema only, no seed data:
kivi reset
```

## Interface to Open

Nothing to launch. Open a terminal in the project root (venv activated) and run the `kivi` commands below.

## Primary Interactions to Try

```bash
kivi inspect                                            # inspect the seeded memory state
kivi learn --asr "ask aditya" --final "Ask Aaditya" --type PERSON   # teach Kivi a correction
kivi process --asr "ask aditya" --fmt "Ask Aditya."     # get the memory-aware transcript
```

If you have no API key, you can still exercise the fast path (no LLM call) with an ASR string that has no phonetic candidates, e.g. `kivi process --asr "open the readme file" --fmt "Open the readme file."` — it returns the text untouched at near-zero latency.

## All CLI Commands

Kivi ships seven core commands:

### 1. Learning New Vocabulary (`kivi learn`)
Extracts entities and contextual triggers from a corrected transcription and saves them to the database. Optionally pass `--type` flags (mapped left-to-right to the extracted entities) to improve disambiguation.
```bash
kivi learn --asr "deploy to the neo them container" --final "deploy to the Neovim container" --type TECH_TERM
```

### 2. Processing Live Transcriptions (`kivi process`)
Takes a raw ASR hypothesis and its baseline formatted text, retrieves matching candidates via local/global context scores, and runs them through the LLM context guard to resolve phonetic collisions safely.
```bash
kivi process --asr "tell atom berg to cache it in read is" --fmt "Tell Adam Berg to cache it in read is."
```

*Outputs:* A JSON response with the `memory_aware` (corrected) string, `latency_ms`, and an `interventions` array justifying any changes made by the guard.

### 3. Inspecting Memory (`kivi inspect`)
Dumps the current state of an entity (or all entities) — context triggers, TF-IDF weights, observation counts, aliases, and confidence scores — ordered by confidence.
```bash
kivi inspect --entity "Redis"
```

### 4. Forgetting Entities (`kivi forget`)
Completely removes an incorrectly learned entity via a cascading delete (canonical entity, phonetic aliases, and all context frequencies).
```bash
kivi forget --entity "Neovim"
```

### 5. Penalizing Interventions (`kivi penalize`)
Soft-decays an entity the LLM applies too aggressively: −0.15 confidence (floored at 0.0) and +1 to `rejected_interventions`, suppressing it without erasing learned context vectors.
```bash
kivi penalize --entity "Neovim"
```

### 6. Database Management (`kivi reset`)
Wipes the local SQLite database and reapplies the base schema. Essential for starting fresh or applying schema changes.
```bash
kivi reset            # clean schema, no data
kivi reset --seed     # clean schema + baseline seed data
```

### 7. Running Evaluations (`kivi eval`)
Executes the evaluation runner over an entire benchmark dataset, computing precision, false-positive rate, latency, token usage, cost, and database growth.
```bash
kivi eval --dataset eval/dataset.json --output eval/results.json
```

## Developer Utilities (`update_seed.py`)

`seeds/default.sql` stores phonetic hashes. Those hashes are produced by the **same `doublemetaphone` Python library** the runtime imports, so seed abbreviations always exactly match runtime lookups. If you add new entities to the seed with empty hash columns, recompute them with:

```bash
python seeds/update_seed.py
```

This rewrites the SQL file in place using the library's own outputs — no hand-rolled metaphone tables to drift apart.

## Evaluation

The complete evaluation lives in `eval/`:

* `eval/dataset.json` — **500** cases: **343** where memory should intervene (direct recall, word-boundary splits, phonetic drift) and **157** where it should deliberately do nothing (dictionary words, weak evidence, cross-domain collisions).
* `eval/runner.py` — the benchmark engine. It bypasses the CLI subprocess overhead and executes against the Python engine directly with `ThreadPoolExecutor` (`max_workers` defaults to 20, configurable via the `MAX_WORKERS` env var).
* `eval/results.json` — the generated evaluation results (committed).

### Exact command to run the evaluation

```bash
kivi eval --dataset eval/dataset.json --output eval/results.json
```

### Where the results are written

Results are written to the path given by `--output`; the command above regenerates `eval/results.json` (the committed file). Each run produces a `summary` block plus a full per-case `traces` array preserving the inputs, expected/actual result, memory candidates, interventions, and per-case latency/token/cost.

### What is measured

* `intervention_accuracy` — useful interventions ÷ expected interventions (true positives).
* `false_positive_rate` — unnecessary interventions ÷ negative cases.
* `p50_latency_ms` — median latency across all cases.
* `total_estimated_tokens` and `total_estimated_cost_usd` — heuristic estimate (see README's "Token & Cost Estimation Discrepancies").
* `database_size_kb` — database growth on disk.

### Benchmark notes (fresh vs committed results)

The committed `eval/results.json` was produced with **`qwen3.6-plus`** using **7 worker threads** (`MAX_WORKERS=7`) on the free API tier (free-tier rate limiting made 20 workers heavy), taking ~26 minutes. The runner defaults to `MAX_WORKERS=20`, which is appropriate for review-grade API keys; with a normal-rate key the suite finishes in a few minutes. Estimations use the rates embedded in `eval/runner.py`: $0.1875 / 1M input tokens and $1.125 / 1M output tokens.

## Resetting the System (Exact Procedure)

```bash
kivi reset          # wipe dynamic memory, reapply clean schema (no seed)
kivi reset --seed   # wipe + reapply schema + reload baseline seed
```

* `kivi reset` fails outright if `src/db/schema.sql` is missing.
* With `--seed`, a missing `seeds/default.sql` is silently ignored (the database is still wiped and the schema applied).

After resetting, you can replay the "Primary Interactions to Try" section above to repeat the full journey.

For any help anywhere in the process, just do `kivi --help`.