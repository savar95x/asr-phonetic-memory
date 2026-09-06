# Kivi Phonetic Memory Layer

This text-to-text pipeline bridges the gap between raw Automatic Speech Recognition (ASR) hypotheses and final formatted text. It acts as a **personalized phonetic memory** system, learning a user's unique vocabulary — names, companies, slang, and domain-specific terms — that standard models frequently transcribe *phonetically* but misspell.

The system builds this memory passively using `kivi learn` (by extracting context around corrections) and applies it dynamically using `kivi process` to correct future transcriptions with context-aware precision, entirely bypassing hardcoded dictionaries.

---

## Three Transcript Levels

Every input the system touches exists at one of three levels (from the assignment brief):

| Level | Example |
| ----- | ------- |
| **1 · ASR output** (raw speech-recognition) | `ask aditya to review the sarvam kiwi service` |
| **2 · Formatted output** (after LLM cleanup) | `Ask Aditya to review the Sarvam Kiwi service.` |
| **3 · Memory-aware output** (after Kivi knows the user) | `Ask Aaditya to review the Sarvam Kivi service.` |

Kivi's job: **reliably turn level 1/2 into level 3, but ONLY when the evidence warrants it.**

---

## Internal Architecture

### The Learning Flow (`kivi learn`)

This flow processes ground-truth corrections to extract, encode, and memorize phonetic patterns.

```
ASR + corrected text
  → 1. Token Alignment      (SequenceMatcher diff → <alias> → <canonical> replaces)
  → 2. Context Extraction   (±4-token window, hard-stopped at clauses, stop-words stripped)
  → 3. Phonetic Encoding    (Double Metaphone full-length keys for canonical + alias)
  → 4. Database Upsert      (idempotent merge: entities / aliases / local TF / global DF / system_stats)
  → 5. Confidence Recalc    (asymptotic exponential curve, observations+1)
```

| Step | What happens |
| ---- | ------------ |
| **1 · Token Alignment** | The raw ASR text and corrected final text are lowercased and tokenized. A Sequence Matcher compares them to isolate exact substrings that were replaced (e.g., `adam berg` → `Atomberg`). |
| **2 · Context Extraction** | For every replaced substring, a sliding window scans up to 4 words backward and forward. It hard-stops at syntactic boundaries (punctuation, conjunctions like `and`, `but`, `because`) so context stays localized. Stop words are stripped. |
| **3 · Phonetic Encoding** | The canonical entity and its ASR alias are run through Double Metaphone. Raw primary and secondary keys are stored verbatim (variable length — e.g. `Atomberg → ATMPRK`, `PostgreSQL → PSTKRSKL`) so seed data and runtime lookups always agree with the same library output. |
| **4 · Database Upsert & TF-IDF Update** | The entity, its semantic `entity_type` (e.g. `PERSON`, `TECH_TERM`), and phonetic alias are saved. Global document frequency (how many total entities / how many share this context word) and local term frequency (how often this entity appeared with the context word) are updated. |
| **5 · Confidence Calculation** | Observation count is incremented and a continuous confidence score is recalculated using an asymptotic exponential curve, preventing single-mistake over-indexing. |

#### How `kivi learn` confidently finds an already-known entity

Learning is an **idempotent upsert**, never a blind insert — re-learning the same correction merges with the existing record instead of duplicating it. Every entity gets a deterministic `id` (`lower(canonical).replace(" ", "_")`), so `Neovim`, `neo vim` and `NEOVIM` all map to the same `neovim` row:

| Store | Behavior on re-learn |
| ----- | -------------------- |
| `entities` | `INSERT ... ON CONFLICT(canonical_form) DO UPDATE` — same canonical merges; `entity_type` is preserved via `COALESCE(?, entity_type)` (never overwritten by `NULL`). |
| `phonetic_aliases` | `INSERT OR IGNORE` — an already-known alias is not re-added. |
| `memory_stats` | `observations_count + 1` and the confidence curve is **recomputed upward** — repeated observations (even in *different* contexts) tighten the `≥ 0.3` retrieval gate. |
| `context_keywords` | `local_frequency + 1` on an existing link; `global_word_stats.entity_count` rises **only the first time** this entity links to that keyword. |
| `system_stats` | `total_entities` refreshed from `COUNT(*)` so IDF math always sees the true denominator. |

Re-running `kivi learn --asr "ask aditya" --final "Ask Aaditya"` therefore doesn't create a second `Aaditya` — it strengthens the existing one, and `kivi inspect` reads back the single merged record.

### The Processing Flow (`kivi process`)

This flow applies memory to live, raw ASR transcripts to resolve phonetic collisions.

```
ASR string
  → 1. N-Gram Generation     (1/2/3-token sliding windows + "squashed" no-space variants)
  → 2. Key Computation       (Double Metaphone for each n-gram & squashed key)
  → 3. Vector Retrieval      (live SQL TF-IDF; threshold ≥0.2, confidence ≥0.3)
  →    ├─ No candidates  → return formatted unchanged, NO LLM call (fast path, ~0ms)
  →    └─ Candidates     → 4. LLM Context Guard → memory-aware output + interventions
```

| Step | What happens |
| ---- | ------------ |
| **1 · N-Gram Generation** | Extracts 1-to-3 token sliding windows from the raw ASR string. |
| **2 · Key Computation & Squashing** | Each n-gram generates standard phonetic keys. Spaces are removed to create "squashed" keys (e.g. `neo them` → `neovim`), computing metaphones for both. |
| **3 · Vector Retrieval (Fast Path)** | The SQLite database performs a live TF-IDF calculation filtering candidates on context overlap. If none clear the threshold (`score ≥ 0.2` and `confidence ≥ 0.3`), the LLM is bypassed entirely → 0ms latency. |
| **4 · Context Guard (LLM Disambiguation)** | If candidates match, the raw ASR, baseline formatted text, and retrieved phonetic candidates (with their `entity_type`) go to an LLM. Driven by strict spelling rules, cross-domain collision checks, and semantic type constraints (grammatical syntax for `PERSON`, strict keywords for `TECH_TERM`), the guard decides whether to intervene, returning structured JSON. The call is made deterministic (`temperature=0.0`, strict JSON mode, `MAX_RETRIES` on the client) so identical inputs produce stable output. |

### The Correction Flow (`kivi forget` / `kivi penalize`)

Manual control over incorrect learnings and misaligned LLM interventions.

| Command | Behavior |
| ------- | -------- |
| **`forget`** (Hard Deletion) | Complete purge of an entity. `ON DELETE CASCADE` wipes all associated aliases, statistical weights, and context keywords in one statement. |
| **`penalize`** (Soft Decay) | Rather than destroying an entity, reduces `confidence_score` by 0.15 and increments `rejected_interventions`. Pushes the entity below the `0.3` retrieval threshold without deleting learned context TF-IDF weights. |

---

## Directory Structure

```
.
├── pyproject.toml              # packaging + the `kivi` console script (Click)
├── .env.example                # API_BASE / API_KEY / MODEL / MAX_WORKERS / MAX_RETRIES template (real key is gitignored in .env)
│
├── README.md                   # ← product documentation (this file)
├── RUN.md                      # the reviewer's runbook — PRIMARY REVIEW METHOD declared here
├── USAGE.md                    # per-command quirks, edge cases & real JSON output shapes
├── ALGORITHMS.md               # "why does it work" explainer (design notes, grounded in src/)
├── todo.md                     # development checklist & review-readiness self-check
│
├── src/                        # the Python engine
│   ├── cli.py                  # Click commands: learn / process / inspect / forget / penalize / reset / eval
│   ├── db/
│   │   ├── client.py           # KiviDB — SQLite connection, TF-IDF SQL, confidence, delete/penalize, inspect
│   │   └── schema.sql          # DDL (6 tables + indexes)
│   └── engine/
│       ├── aligner.py          # learn: diff + context extraction (SequenceMatcher, stop words, boundaries)
│       ├── phonetics.py        # thin wrapper over the doublemetaphone library (full-length keys)
│       ├── memory.py           # process: n-grams + squash → db.get_candidates
│       └── guard.py            # LLM disambiguation (system prompt + env-configurable client)
│
├── seeds/
│   ├── default.sql             # 50 baseline entities + aliases + stats + context (reproducible)
│   └── update_seed.py          # recompute seed hashes with the SAME library used at runtime
│
├── eval/
│   ├── runner.py               # in-process, thread-pooled benchmark → summary + traces
│   ├── dataset.json            # 500 cases (343 positive / 157 negative)
│   └── results.json            # committed generated results (~qwen3.6-plus, 7 workers)
│
├── .kivi/
│   └── memory.db               # the runtime SQLite database (created by `kivi reset`)
```

---

## Algorithms Used

| Algorithm | Role | Why chosen |
| --------- | ---- | ---------- |
| **Double Metaphone (Phonetics)** | Maps words to 1–2 phonetic codes via ~100 spelling rules. | Replaces older algorithms like Soundex; accounts for English/non-English pronunciation irregularity by returning primary + secondary keys. Strictly minimizes false negatives. Keys stored at full library length, keeping storage/retrieval bit-for-bit consistent with the library's own output. |
| **Gestalt Pattern Matching (`difflib.SequenceMatcher`)** | Aligns ASR with Final text during learning. | Chosen over Levenshtein distance because it finds the *longest contiguous matching subsequence*, smoothly handling structural insertions/deletions (dropped ASR words) rather than just character edits. |
| **Smoothed TF-IDF (Context Weighting)** | Ranks candidate entities by surrounding words, computed strictly in SQL. | Formula: `local_frequency × log((total_entities + 2.0) / (entity_count + 1.0))`. A pure frequency count fails (common words drown out signal); TF-IDF boosts unique, domain-specific context words and neutralizes generic ones. |
| **Asymptotic Exponential Decay (Confidence)** | Controls trust in an entity over observations. | Formula: `1.0 − (1.0 − 0.7) · e^(−0.3 · (observations − 1))`. Starts at a base `0.70` (never instantly trusting a single observation) and asymptotically approaches `1.0` as the entity is observed in different contexts. |

---

## Database Schema

Six tables, isolated by concern. `system_stats` and `global_word_stats` exist purely as the numerator/denominator for the SQL-side IDF math; the rest use `ON DELETE CASCADE` so deleting an entity cleans up cleanly.

| Table | Purpose |
| ----- | ------- |
| `entities` | Core of a learned word: `canonical_form`, semantic `entity_type`, primary/secondary metaphones. The root table for foreign keys. |
| `system_stats` | Singleton row tracking `total_entities` — the IDF numerator. |
| `global_word_stats` | Global frequency of context words across all entities — the `entity_count` (IDF denominator). A word shared by many entities (e.g. "the", "said") approaches zero IDF. |
| `phonetic_aliases` | The actual ASR mistakes (`alias`) that led to a correction; maps back to `entity_id`. Enables exact matching to bypass fuzzy logic when a known mistake recurs. |
| `context_keywords` | Many-to-many bridge linking an `entity_id` to a `keyword`, storing `local_frequency` (how often this entity was spoken near this word). |
| `memory_stats` | Tracks `observations_count`, `successful_interventions`, `rejected_interventions`, `confidence_score`. Evaluated at runtime to filter out speculative candidates (≥ `0.3`) before the LLM guard. |

Indexes: `entities(primary_metaphone)`, `phonetic_aliases(primary_metaphone)`, `context_keywords(keyword)`. WAL journal mode + `foreign_keys=ON` + `math.log` registered as `LOG` for in-SQL TF-IDF.

### Code paths at a glance

Where each command actually lives when reading the implementation:

| Command | Call chain |
| ------- | ---------- |
| `kivi process` | `cli.py:process` → `memory.retrieve_candidates(ASR, db)` → sliding 1/2/3-grams (+ squashed) → `db.get_candidates(std, sec)` → SQL TF-IDF CTE (weight ≥ 0.2, confidence ≥ 0.3). No candidates → return formatted unchanged; else `guard.resolve_ambiguity(asr, fmt, candidates)`. |
| `kivi learn` | `cli.py:learn` → `aligner.extract_learning_pairs(ASR, final)` → per pair `phonetics.get_phonetic_keys(canonical)` → `db.learn_entity(...)` idempotent upsert (entities / aliases / local TF / global DF / system_stats / confidence). |
| `kivi inspect` | `client.inspect_entities(...)` — the *same* TF-IDF CTE as `get_candidates` (no threshold), so displayed weights always match retrieval. |
| `kivi forget` | `client.forget_entity(canonical)` → `DELETE FROM entities` → `ON DELETE CASCADE`. |
| `kivi penalize` | `client.penalize_entity(canonical)` → `rejected_interventions + 1`, `confidence − 0.15` floored at 0. |
| `kivi reset [--seed]` | `client.reset(schema.sql)` → executes the DDL (drop/recreate + singleton `system_stats` row); with `--seed`, executes `seeds/default.sql`. |
| `kivi eval` | `eval.runner.run_eval` — `ThreadPoolExecutor` over cases, each worker opening its own `KiviDB` connection, running straight into the engine (no CLI subprocess), dumping `{summary, traces}` to `--output`. |

---

## Decisions, Challenges & Problems Faced

A record of the real problems hit while building this — and the decisions that solved each one.

### Contextualising names (`entity_type`)

Names almost always appear beside *generic*, meaningless words ("met **with** aditya", "aditya **said**..."), so a PERSON's lexical context keywords are weak evidence on their own. The system solves this in two ways:

* **`entity_type` routing in the guard.** `PERSON` candidates are validated with grammatical/syntactic reasoning (agentive verbs, name positions like *"called X"*, *"met with X"*) even when context keywords are empty; `TECH_TERM` candidates demand strict domain-keyword evidence to avoid dictionary-word collisions.
* **`--type` flags (optional hint, not a requirement).** `kivi learn --type PERSON` attaches the type when the caller knows it. The frontend usually won't know the type, so the tool never *requires* it — but when supplied, it's extra context that materially improves the LLM's decision.

### Accidental multi-word splits vs. intended multi-word entities (the dual n-gram key)

ASR can split **one** word into several (`adam berg` → `Atomberg`), but the system must **not** collapse genuinely multi-word entities (`max pain` → `Max Payne`, `crash royal` → `Clash Royale`, `boyd linux` → `Void Linux`) into a single word. `memory.py` therefore computes **both** keys for every 1–3 n-gram:

* a **standard key** preserving word boundaries (matches the intended multi-word entities), and
* a **squashed key** with spaces removed (matches accidentally-split compounds).

Whichever key hits the phonetic index wins — so split compounds are caught *and* true multi-word names stay intact.

### Learning the final word because of a trailing full-stop

Without care, `"...the Kubernetes."` vs `"...the Kubernetes"` looks like a two-word replace and `kubernetes.` gets learned as a bogus entity. Fix: every token is punctuation-stripped **before** diffing, and any pair where `alias.lower() == canonical.lower()` is skipped entirely. Punctuation-only corrections (trailing full-stops included) are therefore never learned — the period stays in the *output* text only, never in memory.

### Generic context noise (`is`, `am`, `the`, `are`, `were`, …)

High-frequency filler words leak into context windows and drown out real signals. Three coordinated defenses:

1. **Exhaustive stop-word list** — ~150 articles, pronouns, prepositions, auxiliary verbs, conjunctions, adverbs and speech fillers (`aligner.py.STOP_WORDS`) are filtered out at learning time.
2. **Frequency weighting** — global **IDF** (*inverse*): a word shared by many entities (e.g. `the`, `said`) gets near-zero weight; local **TF** (*additive*): repeated co-occurrence with *one* entity boosts only that entity.
3. **Strict clause boundaries** — context collection hard-stops at conjunctions and punctuation so it never bleeds across a clause.

### Concurrency because results are slow

The evaluation suite is dominated by external LLM latency, not compute. `eval/runner.py` therefore runs cases in a `ThreadPoolExecutor` (`MAX_WORKERS`), with each worker opening its own `KiviDB` connection for safe SQLite concurrent reads (WAL mode). This collapsed the committed ~26-minute run (7 workers, free tier) into a few minutes on a review-grade key — the concurrency is a direct response to each LLM call taking seconds. (Full provenance: **Benchmark performance** below.)

### Aliases exist because metaphones don't always align

Retrieval matches by **Double Metaphone key** (primary/secondary), never by literal string — so `adam berg`, `atom berg` and `atomburg` all resolve to `Atomberg` via a single alias row. But some sound-alike pairs have *genuinely different* keys (`Cognito` = `KNT/KKNT`, `incognito` = `ANKNT/ANKKNT`); those need an explicit alias row (`incognito → cognito`) to carry the phonetic bridge across keys the algorithm can't derive on its own.

Aliases are written **only at learn time** (`db.learn_entity`) and read **only during retrieval** — `db.get_candidates` keys its WHERE clause on `entities` *and* `phonetic_aliases` metaphones jointly (`client.py`). They never gate learning, inspect, forget, or penalize.

Why not an Indic-phonetic core (e.g. IndicSoundex) instead of Double Metaphone? Double Metaphone is Anglocentric, which is exactly *why* disjoint-key pairs like `Cognito`/`incognito` need the alias bridge. An Indic-aware encoder would collapse more of those — **shrinking** the alias table — but can't **replace** it: the same vocabulary contains global tech terms (`PostgreSQL`, `Grafana`, `Linux`) whose keys such an encoder would mis-derive. Inclusive general core + an exception bridge is the deliberate design.

### Deliberately NOT built: deterministic fast-path rewriting

We considered skipping the LLM whenever evidence is strong enough to rewrite deterministically (cutting latency further). We chose **not** to build it: the guard is exactly the layer that refuses dictionary-word collisions (`kiwi`/`Kivi`, `avoid`/`Void`), and routing every non-zero-candidate hit through it is cheap insurance against false positives. Latency is instead bounded by the zero-candidate fast path (~0ms) and `MAX_WORKERS` concurrency in eval.

### Unlearn & forget (manual correction features)

Hard deletion (`forget`) and soft decay (`penalize`) are the user's manual override pair — see **The Correction Flow** table in *Internal Architecture* for their exact behavior. They exist as an escape hatch when a wrong learning or a misaligned LLM intervention slips through: the system is designed to be *correctable*, not just correct.

### Other decisions

| Challenge | How it was solved |
| --------- | ----------------- |
| **In-Database Math over Python Processing** | Instead of dumping thousands of keyword rows into Python per request, `math.log` is registered into the SQLite connection so candidate filtering runs entirely inside the C-optimized SQL engine → microsecond retrieval. |
| **LLM Over-Correction** | Early iterations saw the LLM replacing valid English words with similar-sounding entities on weak context. Fixed with strict cross-domain collision rules in `guard.py`, `entity_type` semantic parsing, a strict `{output, interventions}` JSON contract, and the `kivi penalize` command to manually decay repeat offenders. |

---

## Limitations, Edge Cases & What Kivi Does Well

### What the system is *good at* — an exhaustive taxonomy of phonetic memory

Kivi's strength is resolving the many ways a spoken term can be transcribed wrong. Below is the complete taxonomy of phonetic-memory cases the system handles — with real examples from `eval/dataset.json` (each maps a mis-transcribed ASR phrase to the corrected entity):

**1. Direct recall — name to known spelling (proper noun / personal name)**
The user's own spelling preference for names, overriding the common/ASR spelling.
- `aditya → Aaditya` ("I have a meeting with aditya.")
- `sever → Savar` ("Sever is leading the backend migration project.")
- `sourav → Saurabh` ("Discuss the engineering roadmap with sourav.")
- `item → IITM` ("The item faculty published breakthrough quantum research.")

**2. Compound & brand word split (ASR inserts a space inside one entity)**
The most common ASR failure — one word broken into two or more by space insertion. Kivi's **squashed-key** detection is built for exactly this.
- `adam berg → Atomberg` (company), `neo them → Neovim`, `cube are net is → Kubernetes`
- `read is → Redis`, `dock her → Docker`, `post man → Postman`, `pan das → Pandas`
- `tea max → Tmux`, `jewel iter → Jupyter`, `pie charm → PyCharm`, `gruff on a → Grafana`
- `pro me the us → Prometheus`, `cough car → Kafka`, `val hime → Valheim`, `max pain → Max Payne`

**3. Phonetic / dialect drift (different but sound-alike words)**
The raw transcription spells a term phonetically ("as it sounds") instead of its canonical spelling.
- `keevee → Kivi`, `dezel → Diesel`, `pie dantick → Pydantic`, `west term → WezTerm`
- `a lack pretty → Alacritty`, `terror form → Terraform`, `soup a base → Supabase`
- `art linux → Arch Linux`, `roast → Rust`, `goroutine-adjacent go lang → Golang`

**4. Acronyms & letter-sequences spoken as words**
Acronyms that, when spoken aloud, produce ordinary words or multi-syllable phrases.
- `item → IITM`, `jason → JSON`, `engine x → Nginx`, `gee are pee see → gRPC`
- `graph ql → GraphQL`, `z shell → Zsh`, `ee lab → IITM`, `read is → Redis` (catches letter-run)

**5. Homophone / dictionary-word collision (valid English word that sounds like a product/name)**
A perfectly valid everyday word that happens to sound like a learned entity. Kivi must decide *without* overcorrecting.
- `avoid → Void (Linux)` vs. `avoid` (the verb) — "We should avoid linux for this project." (correct: do nothing)
- `kiwi → Kivi` vs. *kiwi* (the fruit) — "I bought a fresh kiwi from the market." (correct: do nothing)
- `salary → Celery` vs. *salary* (the pay) — "The average salary for a backend engineer." (correct: do nothing)
- `jason → JSON` vs. *Jason* (a person) — "We need to invite jason to the meeting." (correct: do nothing)

**6. Semantic collision traps (context may be misleading)**
Cases where the surrounding words could fool a naive system, but Kivi's context weights + guard refuse.
- `incognito → Cognito` only in an AWS/auth context; *incognito tab* stays untouched.
- `sable → Sable` (game) vs. *sable antelope* — "The sable antelope is fast." (correct: do nothing)
- `corner → Conda` vs. *corner* of a room; `post man → Postman` vs. *a postal worker*.
- `gruff on a → Grafana` vs. *a gruff old man*; `pie com → Picom` vs. *apple pie*.

**7. Weak-evidence negatives & "deliberately do nothing"**
The system is engineered to *refuse* intervention when evidence is thin — a core design principle from the brief.
- `bob → do nothing`, plain common English ("The quick brown fox...") → no candidates → fast path.
- Valid dictionary words in *technical-looking* but non-matching contexts ("We should avoid creating memory leaks in the container.").

**8. Multi-entity co-occurrence & disambiguation**
When several learned entities appear in one transcript, each is resolved independently and correctly.
- `aditya configured neo them terminal with a jason payload` → `Neovim`.
- `deploy neo them to cube are net is` → both `Neovim` and `Kubernetes` are resolved.

### How the system decides "do nothing"

"Deliberately doing nothing" is engineered at multiple layers, not left to chance:

| Layer | What it filters out |
| ----- | ------------------- |
| No phonetic candidates | Non-matching strings → bypass LLM entirely (fast path). |
| Confidence gate (≥ 0.3) | Single-observation, speculative entities. |
| Weak TF-IDF context | Matching entities whose surrounding words don't fit. |
| LLM cross-domain rules | Valid dictionary words (kiwi, avoid, salary) in non-technical contexts. |

### Known limitations

* **Latency:** While zero-candidate queries safely bypass the LLM (0ms overhead), ambiguous phonetic matches require an external API call, introducing network latency governed by the upstream LLM provider.
* **Collisions:** If two nearly identical phonetic entities (e.g. `Stephen`/`Steven`) share very similar global word statistics, the system leans on the LLM's default spelling rules, which can occasionally cause false positives.
* **N-gram window cap:** The retrieval window is capped at 3 tokens, so a proper noun split into 4+ words will not line up.

### Benchmark performance

| Metric | Value |
| ------ | ----- |
| **Intervention accuracy** (TP) | **87.5%** (500-case stress test) |
| **False positive rate** | **3.2%** |
| **Median (p50) latency** | **23,250ms** (Qwen 3.6 Plus) |
| **Local SQLite retrieval** | consistently **< 5ms** |

**Provenance notes:** The committed `eval/results.json` was generated on the free API tier with **Qwen 3.6 Plus** at **7 concurrent workers** (`MAX_WORKERS=7`) over ~26 minutes. Development started on `qwen3.6-flash` until the free token pool ran out, then shifted to `qwen3.6-plus` for the final benchmark run. The runner defaults to `MAX_WORKERS=20` (configurable via the env var) because the reviewing agent is expected to provide higher-rate API credentials — re-running will be substantially faster than the committed results.

The high benchmark p50 is largely an artifact of free-tier API queuing and concurrency rate-limiting during bulk execution. In standard single-turn CLI usage (`kivi process`), calls typically complete in sub-10 seconds, while local SQLite TF-IDF retrieval consistently executes in under 5ms.

### Token & Cost estimation discrepancies

The evaluation suite reports ~281k estimated tokens ($0.08), whereas upstream API metrics logged ~900k. This arises from:

* **Heuristic vs. Byte-Pair Tokenization:** The runner uses a character-length heuristic (`char_len // 4`), which breaks down on arbitrary Double Metaphone consonant hashes (e.g. `PSTKRSKL`, `ARXLNKS`) and indented JSON schema syntax — these out-of-vocabulary strings split into 1–2 character fragments per token.
* **Prompt & Chat Template Overhead:** OpenAI-compatible wrappers inject role tokens, message delimiters, and formatting templates that raw string-length math omits.

---

## AI Use

Where AI assisted in this repository, transparently:

* **In the product:** the only AI model call in the loop is the LLM context guard (`src/engine/guard.py`), invoked only when phonetic candidates already matched memory. It sends the raw ASR text, the baseline formatted text, and the retrieved candidates to an OpenAI-compatible chat-completions model under a strict JSON contract with `temperature=0.0`. Every other layer — phonetic hashing, TF-IDF scoring, confidence, retrieval — is deterministic and runs locally; zero-candidate queries never reach the model.
* **In building the software:** the majority of the codebase was researched and written with **Gemini 3.1 Pro (web app)** used as the coding assistant, which was also used for debugging and improving output when results weren't up to mark. The author retained the final say on every architectural decision and on system design — the assistant proposed, the author decided.
* **In the documentation:** the docs began as an author-drafted layout and were expanded and refined by a coding agent (**opencode**, free tier) to match the assignment-brief requirements and elaborate the decisions behind the design; the author reviewed and approved the final wording.
