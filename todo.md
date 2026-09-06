# todo.md — development status & review-readiness self-check

A living checklist tracking implementation progress and each requirement of the assignment
brief (Parts One → Four) the repository must satisfy. Kept in-repo so the state of every
deliverable is auditable.

## Progress

- [x] Build the end-to-end phonetic memory layer (learn / process / inspect / forget / penalize / reset / eval).
- [x] Schema: entities, phonetic_aliases, context_keywords, memory_stats, system_stats, global_word_stats (WAL).
- [x] Seed data — 50 entities with aliases, TF/DF context stats, baseline confidence.
- [x] `seeds/update_seed.py` — recompute seed hashes with the exact runtime library so abbreviations never drift.
- [x] Squashed-key trick (atom berg → atomberg) for split compounds.
- [x] In-SQL smoothed TF-IDF (`math.log` registered into SQLite).
- [x] Confidence asymptote (base 0.70, k=0.3) + `penalize` (‑0.15, floor 0) + `rejected_interventions`.
- [x] LLM context guard with entity_type routing (PERSON grammar vs TECH_TERM keywords).
- [x] 500-case eval dataset (343 should-intervene / 157 should-not) + runner + committed results.json.
- [x] README / RUN.md / USAGE.md updated to current reality.
- [x] .env.example points at `qwen3.6-plus` (committed results are from plus at 7 workers).

## Open items / known truths to remember

- [ ] Free API tokens are exhausted — do NOT re-run `kivi eval --dataset eval/dataset.json` unless a fresh key exists. `eval/results.json` is trusted as-is.
- [ ] Model history: started `qwen3.6-flash` (fast/cheap) → hit free-token cap → finished the benchmark on `qwen3.6-plus`, 7 workers (20 caused free-tier rate-limit backoff). Runner ships `max_workers=20` because reviewer keys should handle it.
- [ ] RESULTS PROVENANCE (put this back in docs if regenerating): committed results = plus model, 7 threads, ~26 min.

## Self-check against the evaluator prompt (kept for reference)

**Part One — Core System & Architecture**
- [x] ASR+formatted → memory-aware output.
- [x] Abstraction covers how Kivi learns, what it stores, durability, removal/modification triggers, injection into formatting.
- [x] Explicitly handles weak/wrong evidence (confidence gate, guard refusal, penalize).
- [x] Goes beyond the single example (500 cases, deliberate non-intervention).

**Part Two — Runnable Demonstration**
- [x] Provide observations → `kivi learn`.
- [x] Inspect memory → `kivi inspect`.
- [x] New ASR+formatted → memory-aware → `kivi process`.
- [x] Why did/didn't it intervene → interventions + guard rules (fast-path returns unchanged).
- [x] Reset & repeat → `kivi reset [--seed]`.

**Part Three — Evaluation & Inspectability**
- [x] Success defined (intervention_accuracy / false_positive_rate).
- [x] Cases where memory acts and where it mustn't (343 / 157).
- [x] Per-case audit: inputs, expected, actual, candidates (memory state), interventions+reason.
- [x] Useful vs unnecessary interventions reported separately (TP vs FP).
- [x] Latency / tokens / cost / db growth measured.
- [x] Reproducible (`kivi eval --dataset eval/dataset.json --output eval/results.json`).

**Part Four — Repository & Docs**
- [x] Source, demo, schema, seed, eval dataset, generated results all committed.
- [x] README: product, architecture, decisions, limitations, AI use.
- [x] RUN.md: primary review method + runtimes/versions + every env var + install/migrate/seed commands + processes-to-start + interface to open + interactions + eval command + results location + reset procedure.
- [x] .env.example included; real creds not committed.
- [ ] Double-check RUN.md reads cleanly end-to-end from a fresh clone right before submitting (the agent clones the exact commit SHA).

## Ideas to verify / future investigation

- [ ] Double Metaphone rule internals (why C→K but CH→K/X depending on context, why Spanish/Germanic/J ones differ). Read the reference paper's rule list once, from the library's perspective.
- [ ] SequenceMatcher vs LCSubsequence differences for *structural* ASR insertions — verify by intent instead of luck.
- [ ] SQLite `GROUP_CONCAT` ordering guarantees in the candidate/inspect queries (aliases/keywords order stability).
- [ ] Whether the char//4 token heuristic could be replaced by `tiktoken`-style byte-pair counting without changing reported results.