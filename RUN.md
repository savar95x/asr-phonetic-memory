# RUN.md
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

Kivi operates entirely through a command-line interface, providing five core commands to manage and evaluate your phonetic memory layer:

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

### 4. Database Management (`kivi reset`)

Wipes the local SQLite database and reapplies the base schema. Essential for starting fresh or applying schema migrations.

```bash
kivi reset --seed

```

*(The `--seed` flag safely populates the database with default entities and global stats for immediate testing).*

### 5. Running Evaluations (`kivi eval`)

Executes the evaluation runner over an entire benchmark dataset to calculate precision, recall, false positive rates, and latency profiles.

```bash
kivi eval --dataset tests/eval_data.json --output results.json

```

> [Note]
> For more usage, check out [USAGE.md](USAGE.md)
