from __future__ import annotations
import json
from typing import Dict, List, Any

# ─────────────────────────────────────────────────────────
# Contradiction Detection across agent findings
# ─────────────────────────────────────────────────────────

# Mock contradictions for demo scenarios
MOCK_CONTRADICTIONS = {
    "10mw": [
        {
            "topic": "PJM Interconnection Timeline",
            "claim_a": "PJM interconnection queue backlog is 4-7 years for new large loads in Northern Virginia.",
            "source_a": "PJM Interconnection Queue Reform Report 2026",
            "claim_b": "The typical permit-to-power timeline in Loudoun County is 12-18 months for expansions to existing campuses.",
            "source_b": "CBRE NoVA Data Center Market Report Q1 2026",
            "severity": "high",
            "resolution_strategy": "The 12-18 month timeline assumes existing utility capacity. If substation or transmission upgrades are needed (likely for 10MW), the PJM queue timeline dominates. Verify whether existing campus has pre-approved capacity headroom."
        },
        {
            "topic": "Power Availability vs Market Demand",
            "claim_a": "Available utility power in the Ashburn corridor is effectively zero for new 10MW+ loads without multi-year queue waits.",
            "source_a": "Dominion Energy Loudoun Load Forecast",
            "claim_b": "Powered shell lease rates in the NoVA corridor have reached $170-$200/kW/month — implying active leasing and available capacity.",
            "source_b": "JLL North America Data Center Outlook H1 2026",
            "severity": "medium",
            "resolution_strategy": "The high lease rates reflect pre-committed power from developers who secured grid capacity years ago. New entrants face the queue. The lease market is selling existing allocations, not new utility power."
        },
    ],
    "cooling": [
        {
            "topic": "Cooling Technology Selection",
            "claim_a": "Direct-to-chip (D2C) liquid cooling can handle rack densities of 80-120kW while maintaining PUE below 1.15.",
            "source_a": "CoolIT Systems Technical Whitepaper",
            "claim_b": "Single-phase immersion cooling offers the highest density up to 200kW per tank but requires complete server redesign.",
            "source_b": "GRC Immersion Cooling Case Studies",
            "severity": "low",
            "resolution_strategy": "Not a direct contradiction — different solutions for different density tiers. D2C is the pragmatic retrofit choice; immersion is the long-term maximum-density option. Recommend D2C for existing facilities, evaluate immersion for greenfield."
        },
    ],
}


def detect_contradictions(agent_results: List[Dict[str, Any]], openai_client: Any = None) -> List[Dict[str, Any]]:
    """
    Detects contradictions across agent findings.
    
    Production: LLM pairwise comparison.
    Mock: returns pre-built contradictions.
    """
    from backend.config import settings

    if settings.is_mock_mode or openai_client is None:
        return _mock_detect(agent_results)

    # Production: LLM contradiction detection
    try:
        # Collect all claims
        all_claims = []
        for result in agent_results:
            agent = result.get("agent", "unknown")
            for finding in result.get("findings", []):
                all_claims.append({
                    "agent": agent,
                    "claim": finding.get("claim", ""),
                    "source": finding.get("source_title", ""),
                    "confidence": finding.get("confidence", "medium"),
                })

        if len(all_claims) < 2:
            return []

        claims_json = json.dumps(all_claims, indent=2)
        prompt = f"""You are a research auditor checking for contradictions across findings from multiple specialized agents.

Claims from agents:
{claims_json}

Identify any contradictions, conflicts, or tensions between claims. Look for:
- Different timelines or deadlines
- Conflicting capacity numbers
- Conflicting cost estimates
- Conflicting regulatory interpretations
- Marketing claims vs independent analysis
- Source age mismatches

Return ONLY a JSON object:
{{
  "contradictions": [
    {{
      "topic": "Brief description of the contradicted topic",
      "claim_a": "First claim",
      "source_a": "Source of first claim",
      "claim_b": "Conflicting claim",
      "source_b": "Source of conflicting claim",
      "severity": "high/medium/low",
      "resolution_strategy": "How to resolve or investigate this contradiction"
    }}
  ]
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("contradictions", [])
    except Exception as e:
        print(f"[CONTRADICTIONS] LLM detection failed: {e}. Using mock.")
        return _mock_detect(agent_results)


def _mock_detect(agent_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mock contradiction detection using pre-built data."""
    agents_present = set(r.get("agent", "") for r in agent_results)
    all_text = " ".join(
        f.get("claim", "").lower()
        for r in agent_results for f in r.get("findings", [])
    )

    contradictions = []

    if any(kw in all_text for kw in ["pjm", "interconnect", "10mw", "loudoun", "nova"]):
        contradictions.extend(MOCK_CONTRADICTIONS.get("10mw", []))

    if any(kw in all_text for kw in ["cooling", "immersion", "liquid", "d2c"]):
        contradictions.extend(MOCK_CONTRADICTIONS.get("cooling", []))

    return contradictions
