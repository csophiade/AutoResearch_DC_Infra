from __future__ import annotations
import json
import time
from typing import Dict, List, Any

# ─────────────────────────────────────────────────────────
# Gap Analysis & Follow-Up Research Loop
# ─────────────────────────────────────────────────────────

MOCK_GAPS = {
    "10mw": [
        {
            "topic": "Dominion Energy Interconnection Fee Schedule",
            "reason": "No source found with specific fee amounts for data center interconnection studies in Virginia. Dominion's public tariff references are vague on study costs beyond the $50K-$150K range.",
            "importance": "high",
            "suggested_search": "Dominion Energy Virginia interconnection study fees 2026 data center schedule"
        },
        {
            "topic": "Behind-the-Meter Generation Alternatives",
            "reason": "Agents did not research whether on-site generation (fuel cells, gas turbines) could bypass the PJM interconnection queue entirely.",
            "importance": "medium",
            "suggested_search": "Behind-the-meter generation data center Northern Virginia fuel cell gas turbine regulations"
        },
    ],
    "cooling": [
        {
            "topic": "GPU Warranty Under Liquid Cooling",
            "reason": "No source addressed whether NVIDIA or AMD warranty terms change when GPUs are deployed with third-party liquid cooling solutions.",
            "importance": "medium",
            "suggested_search": "NVIDIA GPU warranty liquid cooling third party CoolIT immersion cooling compatibility"
        },
    ],
}

MOCK_FOLLOWUP_RESULTS = {
    "10mw": [
        {
            "agent": "power",
            "subquestion": "Dominion Energy interconnection fees and behind-the-meter generation options for NoVA data centers",
            "findings": [
                {"claim": "Dominion Energy's System Impact Study for loads 5-20MW costs $75,000-$120,000 with a 120-day study period.", "evidence": "Virginia SCC Case No. PUR-2025-00198 established updated fee schedules for data center interconnection effective January 2026.", "source_title": "Virginia SCC Interconnection Fee Order", "source_url": "https://www.scc.virginia.gov/case/pur-2025-00198", "date": "2025-12", "confidence": "high"},
                {"claim": "Behind-the-meter natural gas fuel cells (Bloom Energy, FuelCell Energy) can provide 1-10MW of baseload power without PJM interconnection, but require Virginia DEQ air permits.", "evidence": "Several NoVA data center operators have deployed Bloom Energy Server installations as supplemental power. These qualify as distributed generation under Virginia Code §56-594.", "source_title": "Bloom Energy Data Center Solutions", "source_url": "https://www.bloomenergy.com/solutions/data-centers", "date": "2026-02", "confidence": "medium"},
            ],
            "open_questions": [],
            "risks": ["Fuel cell natural gas supply may face local opposition"]
        }
    ],
    "cooling": [
        {
            "agent": "cooling",
            "subquestion": "GPU warranty terms under third-party liquid cooling",
            "findings": [
                {"claim": "NVIDIA's Data Center GPU warranty is voided only if physical damage results from a non-certified cooling solution. NVIDIA maintains a 'Certified Cooling Partners' list including CoolIT, Vertiv, and Motivair.", "evidence": "NVIDIA Enterprise Support FAQ and Partner Certification Program documentation.", "source_title": "NVIDIA Enterprise Support — Cooling FAQ", "source_url": "https://www.nvidia.com/enterprise-support/cooling", "date": "2026-01", "confidence": "medium"},
            ],
            "open_questions": [],
            "risks": []
        }
    ],
}


def analyze_gaps(agent_results: List[Dict[str, Any]], contradictions: List[Dict[str, Any]], openai_client: Any = None) -> List[Dict[str, Any]]:
    """
    Identifies missing information or gaps in the research.
    """
    from backend.config import settings

    if settings.is_mock_mode or openai_client is None:
        return _mock_gaps(agent_results)

    # Production: LLM gap analysis
    try:
        findings_summary = json.dumps([
            {"agent": r["agent"], "findings_count": len(r.get("findings", [])),
             "open_questions": r.get("open_questions", []),
             "risks": r.get("risks", [])}
            for r in agent_results
        ], indent=2)
        contradictions_summary = json.dumps(contradictions[:3], indent=2) if contradictions else "None found"

        prompt = f"""You are a research quality auditor for an AI infrastructure research system.

Agent findings summary:
{findings_summary}

Contradictions found:
{contradictions_summary}

Identify 1-3 critical information gaps. Look for:
- Missing cost estimates
- Missing timelines
- No recent sources on a key topic
- Sources only from vendor marketing (no independent analysis)
- Missing regulatory or jurisdictional specifics
- Missing local utility data

Return ONLY a JSON object:
{{
  "gaps": [
    {{
      "topic": "What information is missing",
      "reason": "Why this gap matters",
      "importance": "high/medium/low",
      "suggested_search": "Specific search query to fill this gap"
    }}
  ]
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("gaps", [])
    except Exception as e:
        print(f"[GAPS] LLM gap analysis failed: {e}. Using mock.")
        return _mock_gaps(agent_results)


def _mock_gaps(agent_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mock gap analysis."""
    all_text = " ".join(
        f.get("claim", "").lower()
        for r in agent_results for f in r.get("findings", [])
    )

    if any(kw in all_text for kw in ["pjm", "interconnect", "10mw", "dominion"]):
        return MOCK_GAPS.get("10mw", [])
    if any(kw in all_text for kw in ["cooling", "liquid", "immersion"]):
        return MOCK_GAPS.get("cooling", [])
    return []


def run_followup(gaps: List[Dict[str, Any]], openai_client: Any = None) -> List[Dict[str, Any]]:
    """
    Runs a focused follow-up research pass for the most important gaps.
    Returns additional agent results.
    """
    from backend.config import settings

    if not gaps:
        return []

    # Only follow up on high-importance gaps (max 2)
    high_gaps = [g for g in gaps if g.get("importance") == "high"][:2]
    if not high_gaps:
        high_gaps = gaps[:1]

    print(f"[FOLLOWUP] Running follow-up research on {len(high_gaps)} gaps...")

    if settings.is_mock_mode or openai_client is None:
        time.sleep(1.0)
        all_text = " ".join(g.get("topic", "").lower() for g in gaps)
        if any(kw in all_text for kw in ["dominion", "interconnect", "behind-the-meter", "fee"]):
            return MOCK_FOLLOWUP_RESULTS.get("10mw", [])
        if any(kw in all_text for kw in ["warranty", "cooling", "gpu"]):
            return MOCK_FOLLOWUP_RESULTS.get("cooling", [])
        return []

    # Production: search + extract for each gap
    from backend.agents import run_single_agent
    results = []
    for gap in high_gaps:
        task = {
            "agent": "market",  # Use market agent as general-purpose
            "subquestion": gap.get("suggested_search", gap.get("topic", "")),
            "search_strategy": "Targeted follow-up search",
            "expected_evidence": gap.get("reason", ""),
            "priority": "high"
        }
        result = run_single_agent(task, openai_client)
        results.append(result)
    return results
