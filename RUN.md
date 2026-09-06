# RUN.md

## Primary Review Method

**Local CLI (Python) + embedded SQLite.** Nothing is hosted — learning, inspecting, processing, resetting, and evaluating all happen through `kivi` commands in a terminal.

## Prerequisites

* **Python 3.10+** (developed on 3.14).
* An **OpenAI-compatible API key** for the context-guard LLM (any provider exposing `/v1/chat/completions`; defaults to DashScope Alibaba Cloud compatible mode).
* `git` (to clone).

## Environment Variables

Copy `.env.example` to `.env` and fill in your key. `API_BASE`, `API_KEY`, `MODEL` are **required**; the rest are optional:

| Variable       | Description                                                        | Default |
| -------------- | ------------------------------------------------------------------ | ------- |
| `API_BASE`     | Base URL of the OpenAI-compatible chat completions endpoint.        | —       |
| `API_KEY`      | Your secret key. Never commit the real value — `.env` is gitignored. | —       |
| `MODEL`        | Model id used by the guard (e.g. `qwen3.6-plus`).                  | —       |
| `MAX_WORKERS`  | Concurrent workers for `kivi eval`. Lower to `7` if rate-limited.   | `20`    |
| `MAX_RETRIES`  | Retries per LLM API request.                                       | `2`     |

## Setup

```bash
git clone <repo-url>
cd <repo>
python3 -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env   # then put your real API_KEY inside .env
```

## Database Creation, Migration & Seeding

SQLite needs no migration tool. `src/db/schema.sql` is idempotent DDL — it drops existing tables and recreates them from scratch (all data wiped). `kivi reset` re-applies it; `--seed` then loads the baseline memory from `seeds/default.sql`.

```bash
kivi reset --seed   # create .kivi/memory.db + schema + 50 baseline entities
kivi reset          # schema only, no seed
```

## Interface to Open

Nothing to launch — run `kivi` commands in a terminal (venv activated, project root).

## Primary Interactions to Try

```bash
kivi inspect                                            # inspect seeded memory
kivi learn --asr "ask aditya" --final "Ask Aaditya" --type PERSON   # teach Kivi a correction
kivi process --asr "ask aditya" --fmt "Ask Aditya."     # get the memory-aware transcript
```

No API key? Exercise the fast path (no LLM call) with an ASR string that has no phonetic candidates:
`kivi process --asr "open the readme file" --fmt "Open the readme file."` — returns text untouched at near-zero latency.

## All CLI Commands

```bash
# 1. Learn a correction
kivi learn --asr "deploy to the neo them container" --final "deploy to the Neovim container" --type TECH_TERM

# 2. Process a live transcript (JSON: memory_aware + latency_ms + interventions[])
kivi process --asr "tell atom berg to cache it in read is" --fmt "Tell Adam Berg to cache it in read is."

# 3. Inspect memory
kivi inspect --entity "Redis"        # omit --entity for the full database dump

# 4. Forget an entity (cascading delete)
kivi forget --entity "Neovim"

# 5. Penalize an over-applied entity (−0.15 confidence, floored at 0)
kivi penalize --entity "Neovim"

# 6. Reset the database
kivi reset            # clean schema, no data
kivi reset --seed     # clean schema + baseline seed

# 7. Run the evaluation
kivi eval --dataset eval/dataset.json --output eval/results.json
```

## Seed Maintenance (`update_seed.py`)

`seeds/default.sql` stores phonetic hashes produced by the **same `doublemetaphone` library** the runtime imports, so seed keys always match runtime lookups. When adding entities with empty hash columns, recompute in place:

```bash
python seeds/update_seed.py
```

## Evaluation

* `eval/dataset.json` — **500** cases: **343** should-intervene (direct recall, split compounds, phonetic drift) and **157** should-not (dictionary words, weak evidence, cross-domain collisions).
* `eval/runner.py` — benchmark engine; runs against the Python engine in-process with `ThreadPoolExecutor` (`MAX_WORKERS`).
* `eval/results.json` — committed generated results.

```bash
kivi eval --dataset eval/dataset.json --output eval/results.json   # writes summary + per-case traces
```

**Measured:** `intervention_accuracy` (true positives ÷ expected), `false_positive_rate`, `p50_latency_ms`, `total_estimated_tokens` & `total_estimated_cost_usd` (heuristic — see README "Benchmark"), `database_size_kb`.

**Provenance:** committed results produced with `qwen3.6-plus`, 7 workers, ~26 min on the free tier. Runner defaults to `MAX_WORKERS=20`, suitable for review-grade keys.

## Reset Procedure

```bash
kivi reset          # wipe dynamic memory, clean schema
kivi reset --seed   # wipe + clean schema + baseline seed
```

* Fails outright if `src/db/schema.sql` is missing.
* With `--seed`, a missing `seeds/default.sql` is silently ignored (database still wiped).

Then replay the "Primary Interactions to Try" section to repeat the full journey. For anything else, `kivi --help` lists all commands and `kivi <command> --help` shows each command's flags.