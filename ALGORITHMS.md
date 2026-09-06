# ALGORITHMS.md — "why does it work"

The design explainer behind the system: how and why each algorithm was chosen, grounded in the
actual code in `src/`. Where README says *what* the system does, this file says *why* — and it
is kept reference-accurate against the current implementation.

---

## 1. Token Alignment — `difflib.SequenceMatcher` (NOT Levenshtein)

### The job
When the user corrects an ASR transcript (`--asr`) into final text (`--final`), I need
to isolate *exactly which words changed*, so I can learn `<alias> → <canonical>` pairs.

### What the code actually does (`aligner.py`)
It tokenizes both strings (lowercased, punctuation stripped per-token), then runs
`difflib.SequenceMatcher(None, asr_tokens, final_tokens)` and iterates over
`matcher.get_opcodes()`.

Each opcode is one of:
- `equal` — unchanged
- `insert` / `delete` — one side has words the other doesn't (dropped or added words)
- `replace` — words were swapped

For a `replace` opcode, the ASR slice `i1:i2` is the **alias** and the final slice `j1:j2`
is the **canonical** form. E.g. `"adam berg" → "Atomberg"`.

### Why SequenceMatcher and not Levenshtein / Needleman-Wunsch?
I originally specced a DP edit-distance matrix (Wagner-Fischer / Needleman-Wunsch).
Two practical problems convinced me to switch:

1. **Levenshtein finds the cheapest *character*-edit path**, which is great for spelling,
   but ASR errors are often word-level: words are dropped, reordered, or split. I want the
   **longest block of contiguous matching words** to anchor on, then look at what changed
   *between* anchors. That's literally what SequenceMatcher's "matching blocks" are — it's
   Gestalt pattern matching.
2. **Alignments differ subtly.** With a real edit-distance matrix, a multi-word replace like
   `"talk to adam berg"` → `"Talk to Atomberg"` can be reconstructed as two separate edits
   (`apl→?`) or one clean replace, depending on tie-breaks inside the matrix backtrace.
   SequenceMatcher consistently emits one `replace` opcode spanning `["adam","berg"]` against
   `["Atomberg"]` — exactly the unit I want to learn.

Intuition: SequenceMatcher is "the longest matching subsequence, but *contiguous* blocks of
matching runs win", so it's basically the right tool for diff-style alignment, and Python
ships it in the stdlib, C-optimized.

### Context extraction around the replacement
For the `replace` found at tokens `[i1:i2)` in ASR:
- scan **backwards** from `i1-1` up to `window=4` tokens;
- scan **forwards** from `i2` up to `window=4` tokens;
- **hard-stop** at syntactic boundaries (`and`, `but`, `or`, `because`, `so`, `then`,
  `which`, `however`, `therefore`, `although`, `since`, `unless`, and punctuation) so context
  never bleeds across clauses;
- drop stop words and the alias's own words from the collected context.

These surviving words become the entity's `context_keywords`.

GOTCHA worth remembering: `SequenceMatcher` compares *token lists*, and I already strip
punctuation per token. That means `"Aditya!"` and `"Aditya"` match as `equal` — punctuation
corrections are deliberately **not** learned (`alias.lower() == canonical.lower()` → skip).
This is also what prevents "learning the final word as an entity": `"...the Kubernetes."` vs
`"...the Kubernetes"` diff as equal once the trailing `.` is stripped, so `kubernetes.` can
never be learned as a bogus canonical.

### Why generic filler words never pollute the index (`is`, `am`, `the`, `are`, `were`, …)
Real ASR corrections are surrounded by high-frequency noise, and a naive frequency count lets
those words drown out the signal. Three coordinated defenses, each at a different layer:

1. **Exhaustive stop-word list** — `aligner.py.STOP_WORDS` (~150 entries: pronouns,
   determiners, articles, prepositions, conjunctions, auxiliary/modal verbs, negation
   fragments, conversational fillers) is applied at learning time, so noise rarely enters
   `context_keywords` in the first place.
2. **Frequency weighting** — the local TF is *additive* (repeated co-occurrence with one
   entity strengthens only that entity), while the global IDF is *inverse* (a word shared by
   many entities → near-zero weight). See §4.
3. **Strict clause boundaries** — hard-stops keep context from bleeding across clauses, so a
   word from an unrelated clause can't become a keyword by proximity alone.

Layer 1 stops the noise at the source; layers 2–3 are the backstop if anything slips through.

---

## 2. Phonetic Encoding — Double Metaphone

### The job
Future ASR hits like `"aditya"`, `"atyya"`, `"ahteeatya"` should all point at the same
entity even though the strings differ. Exact string matching fails; I need a *phonetic*
index.

### What Double Metaphone gives
It maps a word to **1–2 phonetic codes** (primary / secondary) using ~100 spelling rules,
phoneme-based (vowels are significant, unlike Soundex). Example outputs from the actual
library (`doublemetaphone` PyPI package), confirmed on this machine:

```
'Aaditya'     ('ATT',   'ATT')
'aditya'      ('ATT',   'ATT')
'Atomberg'    ('ATMPRK','ATMPRK')
'atom berg'   ('ATMPRK','ATMPRK')     <- the KEY trick: same key as 'Atomberg'
'Kubernetes'  ('KPRNTS','KPRNTS')
'cube are net is'  ('KPRNTS','KPRNTS')
'Kivi'        ('KF',    'KF')
'keevee'      ('KF',    'KF')
'Cognito'     ('KNT',   'KKNT')       <- secondary differs!
'incognito'   ('ANKNT', 'ANKKNT')
```

That last pair is important: **Cognito** (`KNT/KKNT`) vs **incognito** (`ANKNT/ANKKNT`)
DON'T share a key by accident, unlike what I might hope — which is exactly why the seed
ships an explicit alias `incognito → cognito`; the alias carries the phonetic bridge.

### Why retrieval matches by the alias's metaphone, not the literal stored word
A stored alias is only ever used for lookup *through its own stored metaphone keys* — the
`get_candidates` WHERE clause compares the input n-gram's keys against `entities` AND
`phonetic_aliases` primary/secondary keys. It never compares literal alias strings. That is
the whole point: one alias row covers *every* spelling variant that shares its phonetics
(`adam berg` vs `atom berg`), so verification happens in phonetic space, never in text space.
(An earlier buggy iteration tried to confirm matches against the literal context word — that
only caught exact string repeats and missed the variants the metaphone index exists to catch.)

### Why the alias exists at all (and why a "better" alphabet wouldn't remove it)
The stack really has two independent sources of truth for "what this entity sounds like": the
entity's own keys and its alias keys. The alias is the load-bearing one: Double Metaphone is
Anglocentric, so morphologically-related spellings can land on **disjoint** key families that
no string-level rule bridges (`Cognito` = `KNT/KKNT`, `incognito` = `ANKNT/ANKKNT`). The alias
row stores the alternate's keys, and retrieval (`db.get_candidates`) ORs alias keys into the
same WHERE clause — so the spoken form resolves even though the two words never share a key.

Could an Indic-phonetic encoder (e.g. IndicSoundex) replace Double Metaphone and kill the table?
Partly: it would collapse more Indic name-variants (`Aaditya`/`Aditya`) into one key and shrink
the alias list — but it can't remove the table entirely, because the vocabulary is not
Indic-only (`PostgreSQL`, `Grafana`, `Linux`, `JSON` are global terms an Indic alphabet would
mis-derive). Double Metaphone stays the inclusive general core; the alias table is the deliberate
exception bridge around its blind spots.

### Why keys are stored at FULL length (not truncated to 4)
The classic Double Metaphone spec caps codes at **4 characters**. This Python library does
**not** necessarily truncate: it returns e.g. `PSTKRSKL` (8 chars) for `PostgreSQL`,
`ATMPRK` (6) for `Atomberg`. `phonetics.py` deliberately returns the library's output
untouched — `primary or ""`, `secondary or primary or ""`.

Why that choice matters:
- If I truncated to 4 chars myself, two genuinely different words could collide more often,
  and worse — the seed file hashes (see below) and runtime hashes could disagree if one side
  truncated and the other didn't.
- Consistency beats cleverness: keep the exact bytes the library emits on **both** the write
  side (learning/seed) and the read side (retrieval).

This is also why `seeds/update_seed.py` exists: it rewrites `seeds/default.sql` hashes by
calling the *same* `doublemetaphone` import at runtime, so the seed's abbreviations can never
drift from what `phonetics.py` computes live. If I hand-wrote `'ATMPRK'` from memory and the
library later changed behavior, lookups would silently miss.

---

## 3. Sliding N-Gram + "Squashed Key" Retrieval (`memory.py`)

### The job
Find entities whose phonetic keys appear somewhere inside a new raw ASR string.

### Steps
1. Tokenize ASR, build **1-, 2-, and 3-grams** (contiguous sliding windows).
2. For each n-gram compute the **standard** phonetic key (`memory.py` keeps this, not just the
   squashed one — it is what matches *intended* multi-word entities like `Max Payne`,
   `Clash Royale`, `Void Linux`, which would be destroyed if we only ever squashed).
3. **Also** compute a *squashed* variant: remove spaces (`"atom berg"` → `"atomberg"`)
   and re-hash. This is the fix for ASR inserting a space inside a single entity.
   The two lookups are done side-by-side and whichever key hits the index wins; results are
   deduplicated per entity id so one entity matched by several n-grams is returned once.

The squash step is the whole reason "Adam Berg" and "Atomberg" hit the same key: the words
individually produce different keys, but the squashed string is a string-level twin of the
canonical entity, so Double Metaphone is evaluated on equivalent input. Keeping the standard
key in parallel is what guarantees we don't "fix" a legitimate multi-word name out of
existence — squashing is an *additional* path, never a replacement.

Limitation I knowingly accept: the window is **capped at 3 tokens**, so a 4+ word split of a
proper noun will never line up.

---

## 4. Smoothed TF-IDF scoring — computed in SQL (`db/client.py`)

### The job
A phonetic collision can have MANY candidate entities. I need the *surrounding words* to rank
them: "check with aditya about the sarvam **service**" should favor `Kivi` (learned near
`sarvam`/`sending`) and `Aaditya`, but not, say, `Atomberg`.

### The formula (per entity × per keyword)
```
weight = local_frequency × log( (total_entities + 2.0) / (entity_count + 1.0) )
```
- `local_frequency` (`context_keywords.local_frequency`) = term frequency within the entity —
  how often this entity was heard near this word.
- `entity_count` (`global_word_stats.entity_count`) = how many *different* entities learned this
  same keyword = the "document frequency".
- `total_entities` (`system_stats.total_entities`) = global denom.

The `+2.0`/`+1.0` smoothing stops `log` from going negative/infinite and avoids division by
zero in tiny DBs. A word shared by many entities (e.g. "linux") gets a near-zero IDF;
a unique word (e.g. "bldc" for Atomberg) keeps a big weight.

### Why in SQL?
- The candidate query filters with `weight >= 0.2` directly inside a CTE, and only rows with
  `confidence_score >= 0.3` survive to the LLM.
- By registering `math.log` as a SQLite function (`conn.create_function("LOG", 1, math.log)`),
  all the math runs inside SQLite's C engine — no pulling thousands of keyword rows into Python
  on every `kivi process` call. Sub-5ms local retrieval.

Personal note — this is the piece I'd most want to re-derive if the DB layer is ever rewritten:
the whole pipeline depends on the CTE doing the same math as the `inspect` query, so they
"feel" consistent (they share the exact same `tfidf_keywords` subquery).

---

## 5. Confidence — the asymptotic exponential curve

```
confidence = 1.0 − (1.0 − 0.7) · e^{−0.3·(observations − 1)}
```
So: 1 observation → 0.70 · 2 → 0.777 · 3 → 0.835 … asymptote 1.0.

Why this shape:
- A single correction should NOT instant-trust an entity (0.7 base, not 1.0).
- Repeated observations in different contexts ramp confidence quickly toward 1.0 but softly.
- `kivi penalize` shaves 0.15 off (floored at 0.0) and bumps `rejected_interventions`,
  letting me manually drag a bad entity back under the 0.3 retrieval gate without deleting it.
- `kivi forget` hard-deletes the entity row; `ON DELETE CASCADE` wipes its aliases,
  memory_stats, and context links in one SQL statement.

---

## 6. The LLM Context Guard (`guard.py`) — the final disambiguation

Even with fast-path key retrieval + TF-IDF ranking, the SQL layer can't decide "is this
`kiwi` the fruit or the product?" That decision is delegated to an LLM with a strict system
prompt. The guard's system prompt is a numbered policy — literally the product's "personality",
the exact rules that decide when to intervene:

1. **DEFAULT TO ORIGINAL** — the (LLM-cleaned) formatted text is usually right; intervene only when justified.
2. **Spelling preferences always apply** — the canonical spelling of the SAME proper name wins ("Stephen" → "Steven" is a persistent user preference, learned via `kivi learn`).
3. **Cross-domain collisions are strictly blocked** unless strong domain keywords appear — don't turn "avoid" into "Void" just because they are phonetic F0/FT cousins.
4. **Fragmentation is confidently corrected** — "neo them" is obviously broken → "Neovim".
5. **"original" must be the exact substring replaced** — every intervention references the precise span it rewrites; nothing is invented outside it.
6. **`entity_type` routing** — `PERSON` uses grammatical/syntactic reasoning (agentive verbs, name positions like "called X"); `TECH_TERM` requires strict keyword context matching.

Why names are routed differently: a person's name almost always sits beside *generic,
lexically-empty* words ("met **with** aditya", "aditya **said**..."), so relying on lexical
context keywords for a `PERSON` would starve it of evidence. Grammar is the only signal that
reliably distinguishes "aditya the person" from "aditya the concept" — hence the syntactic
reasoning branch. (Details in README "Decisions, Challenges & Problems Faced".)

The interaction is made deterministic where the stack allows it: `temperature=0.0`,
`response_format={"type": "json_object"}` (JSON mode), and `MAX_RETRIES` on the client keep
the guard's output stable across identical inputs.

The guard returns `{"output", "interventions":[{original, replacement, matched_context,
confidence, reason}]}`. Zero-candidate hits never reach the LLM — the formatted string is
returned unchanged (~0ms).

---

## 7. Why these choices hold together

Every choice is a *boundary* for when Kivi acts:

| Layer | Decides | Prevents |
| --- | --- | --- |
| SequenceMatcher | WHAT changed | learning punctuation/noise |
| Double Metaphone | WHAT is phonetically similar | false negatives on spelling drift |
| N-gram + squash | WHERE the entity appears | missing split compounds |
| TF-IDF | WHICH entity the context favors | common words drowning signals |
| Confidence | WHETHER to even offer candidates | single-observation over-trust |
| LLM guard | WHETHER to actually intervene | dictionary-word false positives |

"Deliberately doing nothing" is engineered at multiple layers, not left to chance: no
candidates → bypass; weak confidence → filtered; valid dictionary word + weak context → guard
refuses.