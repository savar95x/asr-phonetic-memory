# eval/runner.py
import json
import time
import os
import concurrent.futures
from pathlib import Path
from src.db.client import KiviDB
from src.engine.memory import retrieve_candidates
from src.engine.guard import resolve_ambiguity

# Estimated character length of the system prompt inside src/engine/guard.py
SYSTEM_PROMPT_LEN = 1745 

def evaluate_single_case(case):
    # Instantiate DB per-thread to safely handle SQLite concurrent reads
    db = KiviDB()
    
    start_time = time.time()
    asr = case['asr']
    fmt = case['fmt']
    expected_target = case.get('expected_target')
    
    # 1. Execute phonetic retrieval directly
    candidates = retrieve_candidates(asr, db)
    
    # 2. Fast-path exit (0ms LLM overhead)
    if not candidates:
        return case, {
            "asr": asr,
            "formatted": fmt,
            "memory_aware": fmt,
            "expected_target": expected_target,
            "candidates": [],
            "interventions": [],
            "latency_ms": int((time.time() - start_time) * 1000),
            "estimated_tokens": 0,
            "estimated_cost_usd": 0.0
        }

    # 3. Direct LLM execution
    try:
        decision = resolve_ambiguity(asr, fmt, candidates)
    except Exception as e:
        decision = {"output": fmt, "interventions": [], "error": str(e)}
        
    # Estimate tokens and cost (assuming 1 token ~= 4 chars)
    # Using Qwen 3.6 Flash pricing: $0.1875/1M input, $1.125/1M output
    user_prompt = f"""ASR Input: "{asr}"\nFormatted Input: "{fmt}"\nCandidates from Memory:\n{json.dumps(candidates, indent=2)}"""
    
    input_text_length = SYSTEM_PROMPT_LEN + len(user_prompt)
    output_text_length = len(json.dumps(decision))
    
    est_input_tokens = input_text_length // 4
    est_output_tokens = output_text_length // 4
    
    est_cost = (est_input_tokens / 1_000_000 * 0.1875) + (est_output_tokens / 1_000_000 * 1.125)
        
    return case, {
        "asr": asr,
        "formatted": fmt,
        "memory_aware": decision.get("output", fmt),
        "expected_target": expected_target,
        "candidates": candidates,
        "interventions": decision.get("interventions", []),
        "latency_ms": int((time.time() - start_time) * 1000),
        "estimated_tokens": est_input_tokens + est_output_tokens,
        "estimated_cost_usd": est_cost,
        "error": decision.get("error")
    }

def run_eval(dataset_path: str, output_path: str):
    with open(dataset_path, 'r') as f:
        test_cases = json.load(f)
        
    metrics = {
        "true_positive": 0, "false_positive": 0, 
        "expected_interventions": 0, "negative_cases": 0,
        "latencies": [],
        "total_tokens": 0,
        "total_cost": 0.0
    }
    
    results = []
    
    # Map guarantees the exact original JSON array order is preserved
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for case, output in executor.map(evaluate_single_case, test_cases):
            is_negative = case['expected_target'] is None
            
            if is_negative:
                metrics["negative_cases"] += 1
            else:
                metrics["expected_interventions"] += 1
                
            metrics["latencies"].append(output["latency_ms"])
            metrics["total_tokens"] += output.get("estimated_tokens", 0)
            metrics["total_cost"] += output.get("estimated_cost_usd", 0.0)
            
            interventions = output.get("interventions", [])
            intervened = len(interventions) > 0
            
            if intervened and not is_negative:
                found = any(
                    (inv.get("replacement") or inv.get("target", "")).lower() == case['expected_target'].lower()
                    for inv in interventions
                )
                if found:
                    metrics["true_positive"] += 1
            elif intervened and is_negative:
                metrics["false_positive"] += 1
                
            results.append(output)
            
    p50_latency = sorted(metrics["latencies"])[len(metrics["latencies"])//2] if metrics["latencies"] else 0
    accuracy = metrics["true_positive"] / max(1, metrics["expected_interventions"]) if metrics["expected_interventions"] else 0
    fpr = metrics["false_positive"] / max(1, metrics["negative_cases"]) if metrics["negative_cases"] else 0
    
    # Calculate database size
    db_path = Path(".kivi/memory.db")
    db_size_kb = os.path.getsize(db_path) / 1024 if db_path.exists() else 0.0
    
    summary = {
        "intervention_accuracy": accuracy,
        "false_positive_rate": fpr,
        "p50_latency_ms": p50_latency,
        "total_estimated_tokens": metrics["total_tokens"],
        "total_estimated_cost_usd": round(metrics["total_cost"], 6),
        "database_size_kb": round(db_size_kb, 2)
    }
    
    with open(output_path, 'w') as f:
        json.dump({"summary": summary, "traces": results}, f, indent=2)
