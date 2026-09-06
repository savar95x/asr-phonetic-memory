# Kivi - Phonetic Memory Layer

Kivi turns speech into text across a person's computer. An ASR model hears the words; a language model cleans and structures them; then this system — the phonetic memory layer — corrects personal terms that standard models misspell.

Three transcript levels matter:

1. **ASR output** — raw text from the speech-recognition model
2. **Formatted output** — cleaned and punctuated by the language model
3. **Memory-aware output** — corrected once Kivi knows the relevant personal terms

Example: `ask aditya to review the sarvam kiwi service` → `Ask Aditya to review the Sarvam Kiwi service.` → `Ask Aaditya to review the Sarvam Kivi service.`

The system learns passively via `kivi learn` and applies corrections dynamically via `kivi process`, entirely bypassing hardcoded dictionaries.

> [Note]
> "Kivi" here refers to this project itself, and not Sarvam's Kivi, which is a more polished and complete speech-to-text product.
> The kivi here deals only with the phonetic memory layer of Sarvam's Kivi.

## Directory Structure

```
.
├── pyproject.toml              # packaging + the `kivi` console script (Click)
├── .env.example                # API_BASE / API_KEY / MODEL / MAX_WORKERS / MAX_RETRIES template
│
├── README.md                   # this file
├── RUN.md                      # reviewer runbook — primary review method declared here
├── USAGE.md                    # per-command reference, edge cases, output shapes
│
├── src/                        # the Python engine
│   ├── cli.py                  # Click commands: learn / process / inspect / forget / penalize / reset / eval
│   ├── db/
│   │   ├── client.py           # KiviDB — SQLite, TF-IDF SQL, confidence, delete/penalize, inspect
│   │   └── schema.sql          # DDL (6 tables + indexes)
│   └── engine/
│       ├── aligner.py          # learn: diff + context extraction (SequenceMatcher, stop words, boundaries)
│       ├── phonetics.py        # thin wrapper over the doublemetaphone library (full-length keys)
│       ├── memory.py           # process: n-grams + squash → db.get_candidates
│       └── guard.py            # LLM disambiguation (system prompt + env-configurable client)
│
├── seeds/
│   ├── default.sql             # 50 baseline entities + aliases + stats + context
│   └── update_seed.py          # recompute seed hashes with the same library used at runtime
│
├── eval/
│   ├── runner.py               # in-process, thread-pooled benchmark → summary + traces
│   ├── dataset.json            # 500 cases (343 positive / 157 negative)
│   └── results.json            # committed generated results
│
└── .kivi/
    └── memory.db               # the runtime SQLite database (created by `kivi reset`)
```

## Architecture

### Learning Flow (`kivi learn`)

Processes ground-truth corrections to extract, encode, and memorize phonetic patterns.

```
ASR + corrected text
  → 1. Token Alignment      (SequenceMatcher diff → alias → canonical replacements)
  → 2. Context Extraction   (±4-token window, hard-stopped at clauses, stop-words stripped)
  → 3. Phonetic Encoding    (Double Metaphone full-length keys for canonical + alias)
  → 4. Database Upsert      (idempotent merge: entities / aliases / local TF / global DF / system_stats)
  → 5. Confidence Recalc    (asymptotic exponential curve, observations+1)
```

Learning is idempotent — re-learning the same correction merges with the existing record instead of duplicating it. Every entity gets a deterministic ID (`lower(canonical).replace(" ", "_")`), so `Neovim`, `neo vim` and `NEOVIM` all map to the same row.

### Processing Flow (`kivi process`)

Applies memory to live ASR transcripts to resolve phonetic collisions.

```
ASR string
  → 1. N-Gram Generation     (1/2/3-token sliding windows + squashed no-space variants)
  → 2. Key Computation       (Double Metaphone for each n-gram & squashed key)
  → 3. Vector Retrieval      (live SQL TF-IDF; threshold ≥0.2, confidence ≥0.3)
  →    ├─ No candidates  → return formatted unchanged, NO LLM call (fast path, ~0ms)
  →    └─ Candidates     → 4. LLM Context Guard → memory-aware output + interventions
```

Zero-candidate queries bypass the LLM entirely. When candidates exist, the guard uses `temperature=0.0`, strict JSON mode, and configurable retries so identical inputs produce stable output.

### Correction Flow (`kivi forget` / `kivi penalize`)

Manual control over incorrect learnings and misaligned interventions:

| Command | Behavior |
| ------- | -------- |
| **`forget`** | Hard deletion — `ON DELETE CASCADE` wipes entity, aliases, stats, and context keywords. |
| **`penalize`** | Soft decay — reduces confidence by 0.15 (floored at 0.0), increments `rejected_interventions`. |

## Algorithms

| Algorithm | Role |
| --------- | ---- |
| **Double Metaphone** | Maps words to 1–2 phonetic codes via ~100 spelling rules. Primary + secondary keys stored at full library length for consistency between learning and retrieval. |
| **Gestalt Pattern Matching** (`difflib.SequenceMatcher`) | Aligns ASR with final text during learning. Finds the longest contiguous matching subsequence, handling word-level insertions/deletions better than character-level edit distance. |
| **Smoothed TF-IDF** | `weight = local_frequency × log((total_entities + 2.0) / (entity_count + 1.0))`. Computed entirely in SQL via registered `math.log` — no Python-side row materialization. Filters on `weight ≥ 0.2` and `confidence ≥ 0.3`. |
| **Asymptotic Exponential Confidence** | `confidence = 1.0 − (1.0 − 0.7) · e^(−0.3 · (observations − 1))`. Starts at 0.70 (never trusts a single observation), asymptotes to 1.0. |
| **Dual N-Gram Keys** | Every 1–3 n-gram generates both a standard (space-preserving) key and a squashed (no-space) key. Catches split compounds (`adam berg → Atomberg`) without destroying true multi-word entities (`Max Payne`). |

## Key Design Decisions

- **entity_type routing in the guard** — `PERSON` candidates are validated with grammatical/syntactic reasoning (agentive verbs, name positions) even when context keywords are empty; `TECH_TERM` candidates demand strict domain-keyword evidence.
- **Punctuation immunity** — Tokens are punctuation-stripped before diffing, so `"Kubernetes."` vs `"Kubernetes"` diff as equal. Trailing periods are never learned as entities.
- **Stop-word filtering** — ~150 entries filtered at learning time; TF-IDF further suppresses generic context words. Clause-boundary hard-stops prevent context bleeding across clauses.
- **In-database math** — `math.log` is registered into SQLite so candidate filtering runs entirely in the C-optimized SQL engine. Sub-5ms local retrieval.
- **Aliases bridge disjoint keys** — Some sound-alike pairs (e.g., `Cognito`/`incognito`) produce genuinely different Double Metaphone keys. Explicit alias rows carry the phonetic bridge the algorithm can't derive on its own.
- **No deterministic rewriting** — Every candidate hit goes through the LLM guard. The guard is the layer that refuses dictionary-word collisions (`kiwi`/`Kivi`, `avoid`/`Void`), making it cheap insurance against false positives.

## Database Schema

Six tables, isolated by concern:

| Table | Purpose |
| ----- | ------- |
| `entities` | Core: `canonical_form`, `entity_type`, primary/secondary metaphones. Root for foreign keys. |
| `system_stats` | Singleton row — `total_entities` (IDF numerator). |
| `global_word_stats` | Global frequency of context words — `entity_count` (IDF denominator). |
| `phonetic_aliases` | ASR mistakes (`alias`) mapped to `entity_id` via metaphone keys. |
| `context_keywords` | Many-to-many: `entity_id` ↔ `keyword` with `local_frequency`. |
| `memory_stats` | `observations_count`, `successful_interventions`, `rejected_interventions`, `confidence_score`. |

Indexes: `entities(primary_metaphone)`, `phonetic_aliases(primary_metaphone)`, `context_keywords(keyword)`. WAL journal mode + `foreign_keys=ON`.

## Limitations

- **Latency** — Zero-candidate queries bypass the LLM (0ms); ambiguous matches require an external API call.
- **Collisions** — Nearly identical phonetic entities with similar statistics can cause occasional false positives.
- **N-gram cap** — Retrieval window capped at 3 tokens; a proper noun split into 4+ words won't match.

## Benchmark

| Metric | Value |
| ------ | ----- |
| Intervention accuracy (TP) | **87.5%** (500-case test) |
| False positive rate | **3.2%** |
| Median latency (p50) | **23,250ms** (Qwen 3.6 Plus) |
| SQLite retrieval | **< 5ms** |

Committed `eval/results.json` generated with `qwen3.6-plus` at 7 workers (~26 min on free tier). Runner defaults to `MAX_WORKERS=20` for review-grade keys.

Token cost estimate (~281k tokens, $0.08) under-reports vs. API-reported ~900k for two reasons:

- **Heuristic vs. byte-pair tokenization:** `eval/runner.py` estimates tokens as `char_len // 4`. That breaks on out-of-vocabulary strings like Double Metaphone consonant hashes (`PSTKRSKL`, `ARXLNKS`) and indented JSON schema syntax, which BPE splits into 1–2 character fragments per token.
- **Prompt & chat template overhead:** OpenAI-compatible wrappers inject role tokens, message delimiters, and formatting templates that raw string-length math omits.

## AI Use

- **In the product:** The LLM context guard (`src/engine/guard.py`) is the only AI model call in the loop. It runs only when phonetic candidates match, sending raw ASR text, formatted text, and candidates to an OpenAI-compatible model at `temperature=0.0`. Every other layer — phonetic hashing, TF-IDF scoring, confidence, retrieval — is deterministic and local. Zero-candidate queries never reach the model.
- **In building the software:** Initial research and codebase structure were developed with Gemini 3.1 Pro. All architectural decisions and system design were made by me.
- **In the documentation:** I wrote the basic structure; docs were expanded and refined by a coding agent (opencode, free tier).

All debugging and architectural decisions were mine — AI suggested, but I researched and built only what was needed, balancing accuracy and UX.
