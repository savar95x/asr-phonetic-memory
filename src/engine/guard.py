# src/engine/guard.py
import json
import os
from typing import List
from openai import OpenAI

def resolve_ambiguity(asr: str, fmt: str, candidates: List[dict]) -> dict:
    client = OpenAI(
        base_url=os.environ["API_BASE"],
        api_key=os.environ["API_KEY"],
        max_retries=2
    )
    
    system_prompt = """You are a phonetic memory disambiguation guard for an ASR formatting pipeline.
Your task is to correct phonetic mistranscriptions in the "Formatted Input" using canonical entities from memory.

OPERATIONAL RULES:
1. DEFAULT TO ORIGINAL: ASR systems are usually correct.
2. SPELLING PREFERENCES (ALWAYS APPLY): If the original text and the canonical entity are just different spellings of the SAME proper name (e.g., "Stephen" -> "Steven"), always apply the replacement. This represents a learned user preference.
3. CROSS-DOMAIN COLLISIONS (STRICT): If replacing a valid dictionary word or common name with a completely different technical concept (e.g., or "avoid" to "Void"), YOU MUST NOT REPLACE IT unless strong domain keywords are present in the text.
4. FRAGMENTATION: If the ASR text is an unnatural fragmentation or obvious transcription error (e.g., "neo them"), confidently replace it with the canonical entity.
5. EXACT SPAN: "original" must capture the exact substring being replaced.
6. ENTITY TYPE USAGE: You receive an `entity_type` for each candidate:
   - For `PERSON`: Use grammatical and syntactic reasoning (e.g., look for agentive verbs, proper noun placements like "called X", "met with X", or subject/object structuring) to validate the entity, even if context keywords are empty.
   - For `TECH_TERM`: Enforce strict context keyword matching. Only replace if strong domain/technical keywords are present in the text to avoid collisions with common English words.

OUTPUT FORMAT:
Return strictly valid JSON with no conversational prefix or markdown formatting beyond the JSON block:
{
  "output": "<fully corrected formatted input>",
  "interventions": [
    {
      "original": "<exact substring replaced>",
      "replacement": "<canonical entity name>",
      "matched_context": ["<keyword1>", "<keyword2>"],
      "confidence": <float between 0.00 and 1.00 representing certainty>,
      "reason": "<brief justification>"
    }
  ]
}

If no interventions apply, return "output" matching the exact Formatted Input and "interventions" as []."""

    user_prompt = f"""ASR Input: "{asr}"
Formatted Input: "{fmt}"
Candidates from Memory:
{json.dumps(candidates, indent=2)}"""

    try:
        response = client.chat.completions.create(
            model=os.environ["MODEL"],
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        data = json.loads(response.choices[0].message.content)
        
        if "output" not in data:
            data["output"] = fmt
        if "interventions" not in data:
            data["interventions"] = []
            
        return data
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"output": fmt, "interventions": [], "error": str(e)}
