# eval/runner.py
import json
import time
import concurrent.futures
from src.db.client import KiviDB
from src.engine.memory import retrieve_candidates
from src.engine.guard import resolve_ambiguity

def evaluate_single_case(case):
    # Instantiate DB per-thread to safely handle SQLite concurrent reads
    db = KiviDB()
    
    start_time = time.time()
    asr = case['asr']
    fmt = case['fmt']
    
    # 1. Execute phonetic retrieval directly
    candidates = retrieve_candidates(asr, db)
    
    # 2. Fast-path exit (0ms LLM overhead)
    if not candidates:
        return case, {
            "asr": asr,
            "formatted": fmt,
            "memory_aware": fmt,
            "interventions": [],
            "latency_ms": int((time.time() - start_time) * 1000)
        }

    # 3. Direct LLM execution
    try:
        decision = resolve_ambiguity(asr, fmt, candidates)
    except Exception as e:
        decision = {"output": fmt, "interventions": [], "error": str(e)}
        
    return case, {
        "asr": asr,
        "formatted": fmt,
        "memory_aware": decision.get("output", fmt),
        "interventions": decision.get("interventions", []),
        "latency_ms": int((time.time() - start_time) * 1000)
    }

def run_eval(dataset_path: str, output_path: str):
    with open(dataset_path, 'r') as f:
        test_cases = json.load(f)
        
    metrics = {
        "true_positive": 0, "false_positive": 0, 
        "expected_interventions": 0, "negative_cases": 0,
        "latencies": []
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
    
    summary = {
        "intervention_accuracy": accuracy,
        "false_positive_rate": fpr,
        "p50_latency_ms": p50_latency
    }
    
    with open(output_path, 'w') as f:
        json.dump({"summary": summary, "traces": results}, f, indent=2)
