import asyncio
from app.services.nebius import get_nebius_client
import json

async def test():
    client = get_nebius_client()
    
    prompt = """You are COSKA, an autonomous incident intelligence system performing root cause analysis.

INCIDENT:
  ID: TEST-1
  Service: payment-api
  Severity: CRITICAL
  Description: Test incident

TIMELINE:
  2026-10-29T10:10:00 [DEPLOYMENT] Deployment v1.8.2: Deployed
  2026-10-29T10:15:00 [FIRST_ANOMALY] First pool error: Pool exhausted

EVIDENCE (2 items):
  E-1 [LOG] (conf: 90%): connection pool exhausted
  E-2 [CONFIG] (conf: 100%): DB_POOL_SIZE=5

HYPOTHESES (2):
  H-1: Pool exhaustion (conf: 90%, status: SUPPORTED)
  H-2: DB saturation (conf: 10%, status: REJECTED)

TASK: Determine the root cause based on ALL evidence. You must:
1. Identify the single strongest root cause explanation
2. List supporting evidence IDs
3. List contradicting evidence IDs
4. List rejected hypotheses with reasoning
5. Assign confidence (0.0-1.0)
6. Note any remaining uncertainty
7. Recommend a specific remediation

CRITICAL RULES:
- If evidence is insufficient for a confident conclusion, set confidence < 0.5 and uncertainty = "INSUFFICIENT_EVIDENCE"
- Do not hallucinate. Only use provided evidence.
- The root cause must be traceable to specific evidence IDs.
- Distinguish between correlation and causation.

Return ONLY valid JSON with this exact structure:
{
  "root_cause": "string",
  "confidence": 0.0,
  "supporting_evidence_ids": ["E-XXX"],
  "contradicting_evidence_ids": ["E-XXX"],
  "rejected_hypotheses": [
    {"id": "H-XXX", "reason": "string"}
  ],
  "uncertainty": "string or null",
  "recommended_remediation": {
    "description": "string",
    "exact_change": "string",
    "expected_effect": "string",
    "risk": "LOW|MEDIUM|HIGH",
    "blast_radius": "string",
    "rollback_plan": "string"
  }
}"""
    
    messages = [
        {'role': 'system', 'content': 'You are COSKA, an expert root cause analyst. Return only valid JSON. Be precise and evidence-driven.'},
        {'role': 'user', 'content': prompt}
    ]
    
    client = get_nebius_client()
    result = await client.chat_completion(messages, temperature=0.1, max_tokens=3000)
    print('Result keys:', result.keys())
    content = result['choices'][0]['message']['content']
    print('Content length:', len(content))
    print('Content type:', type(content))
    print('Content start:', content[:100])
    print('Content end:', content[-50:])
    
    # Try parsing like the root cause engine
    start = content.find('{')
    end = content.rfind('}') + 1
    print('Start:', start, 'End:', end)
    if start >= 0 and end > start:
        try:
            parsed = json.loads(content[start:end])
            print('Parsed successfully!')
            print('Keys:', parsed.keys())
        except json.JSONDecodeError as e:
            print('JSON decode error:', e)
            print('Error position:', e.pos)
            problematic = content[start:end][e.pos:e.pos+20]
            print('Problematic char:', problematic)

asyncio.run(test())