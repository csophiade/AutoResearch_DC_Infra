from __future__ import annotations
import json
from typing import Dict, List, Any

# ─────────────────────────────────────────────────────────
# Structured Analyst Briefing Generator
# ─────────────────────────────────────────────────────────

def generate_briefing(
    query: str,
    agent_results: List[Dict[str, Any]],
    contradictions: List[Dict[str, Any]],
    gaps: List[Dict[str, Any]],
    followup_results: List[Dict[str, Any]],
    evidence_graph: Dict[str, Any],
    openai_client: Any = None
) -> Dict[str, Any]:
    """
    Generates a structured analyst-style briefing from all pipeline outputs.
    
    Returns a dict with sections: executive_summary, direct_answer, key_findings,
    evidence_table, contradictions_section, open_questions, next_steps, sources, spoken_summary
    """
    from backend.config import settings

    if settings.is_mock_mode or openai_client is None:
        return _mock_briefing(query, agent_results, contradictions, gaps, followup_results)

    # Production: LLM synthesis
    try:
        return _llm_briefing(query, agent_results, contradictions, gaps, followup_results, openai_client)
    except Exception as e:
        print(f"[BRIEFING] LLM synthesis failed: {e}. Using mock.")
        return _mock_briefing(query, agent_results, contradictions, gaps, followup_results)


def _collect_all_sources(agent_results: List[Dict[str, Any]], followup_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate and collect all sources."""
    seen = set()
    sources = []
    for results in [agent_results, followup_results]:
        for r in results:
            for f in r.get("findings", []):
                url = f.get("source_url", "")
                if url and url not in seen:
                    seen.add(url)
                    sources.append({
                        "title": f.get("source_title", "Unknown"),
                        "url": url,
                        "date": f.get("date", ""),
                        "content": f.get("evidence", "")[:150],
                    })
    return sources


def _collect_all_findings(agent_results: List[Dict[str, Any]], followup_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collect all findings with agent attribution."""
    findings = []
    for r in agent_results + followup_results:
        agent = r.get("agent", "unknown")
        for f in r.get("findings", []):
            findings.append({
                "agent": agent,
                "claim": f.get("claim", ""),
                "source": f.get("source_title", ""),
                "confidence": f.get("confidence", "medium"),
            })
    return findings


def _mock_briefing(query: str, agent_results: List[Dict[str, Any]], contradictions: List[Dict[str, Any]], gaps: List[Dict[str, Any]], followup_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a structured briefing from mock data."""
    sources = _collect_all_sources(agent_results, followup_results)
    all_findings = _collect_all_findings(agent_results, followup_results)
    all_open_qs = []
    for r in agent_results + followup_results:
        all_open_qs.extend(r.get("open_questions", []))

    q = query.lower()
    
    # 10MW NoVA Demo briefing
    if any(kw in q for kw in ["10mw", "10 mw", "power", "northern virginia"]):
        executive_summary = "Adding 10MW of power to an AI data center in Northern Virginia is feasible but faces a 3-5 year critical path dominated by PJM interconnection queue delays and transformer equipment lead times. Regulatory approvals in Loudoun County add 12-18 months. Behind-the-meter fuel cell generation offers a partial bypass strategy."
        direct_answer = "The primary blockers for a 10MW expansion in NoVA are: (1) PJM interconnection queue backlog of 4-7 years, (2) 345kV autotransformer lead times of 110-140 weeks, (3) Loudoun County Special Exception permit process of 12-18 months, and (4) Virginia DEQ environmental review for backup generators. The most viable acceleration strategy is deploying behind-the-meter fuel cells (Bloom Energy) for 1-10MW while waiting for grid interconnection."
        spoken_summary = "I've completed the analysis. Adding 10 megawatts in Northern Virginia faces a 3 to 5 year timeline, mainly due to PJM grid queue backlogs and transformer lead times. Loudoun County permits add 12 to 18 months. Behind-the-meter fuel cells could provide a partial bypass. The full briefing covers interconnection fees, regulatory steps, and market conditions."
    elif any(kw in q for kw in ["cooling", "densif", "rack"]):
        executive_summary = "High-density AI racks exceeding 40kW require liquid cooling. Direct-to-chip (D2C) cooling from CoolIT or ZutaCore handles 80-120kW per rack and is the most practical retrofit option. Immersion cooling reaches 200kW but requires full server redesign. NVIDIA Blackwell B200 systems drive 70-100kW per rack, making liquid cooling mandatory."
        direct_answer = "For rack densification, deploy direct-to-chip liquid cooling (CoolIT, ZutaCore) for existing facilities — it handles 80-120kW per rack at PUE below 1.15. Use rear-door heat exchangers (Vertiv, Motivair) as a quick retrofit for up to 45kW per rack. Reserve immersion cooling for greenfield builds targeting maximum density. Verify GPU warranty compatibility with NVIDIA's Certified Cooling Partners list."
        spoken_summary = "The analysis shows that high-density AI racks need liquid cooling. Direct-to-chip solutions from CoolIT handle 80 to 120 kilowatts per rack. Rear-door heat exchangers are the easiest retrofit. Immersion cooling gets the highest density but requires complete server redesign. Check the full briefing for warranty implications and cost comparisons."
    else:
        executive_summary = f"Research analysis completed for: {query}. Multiple specialized agents investigated the topic across power, compute, cooling, networking, regulatory, and market dimensions."
        direct_answer = f"Based on {len(all_findings)} findings across {len(agent_results)} specialized agents, the research indicates evolving constraints and opportunities in this domain."
        spoken_summary = f"I've completed the research on your question. The analysis covers {len(all_findings)} key findings from {len(agent_results)} specialized agents. Check the full briefing for detailed evidence and recommendations."

    return {
        "executive_summary": executive_summary,
        "direct_answer": direct_answer,
        "key_findings": all_findings,
        "evidence_table": all_findings,
        "contradictions_section": contradictions,
        "open_questions": all_open_qs[:6],
        "next_steps": [
            "Verify the most critical findings with primary source documents",
            "Engage directly with the relevant utility provider for current timelines",
            "Request updated quotes from equipment vendors for current lead times",
            "Consult with local counsel on regulatory approval processes",
        ],
        "sources": sources,
        "spoken_summary": spoken_summary,
    }


def _llm_briefing(query: str, agent_results: List[Dict[str, Any]], contradictions: List[Dict[str, Any]], gaps: List[Dict[str, Any]], followup_results: List[Dict[str, Any]], openai_client: Any) -> Dict[str, Any]:
    """Generate briefing via LLM."""
    sources = _collect_all_sources(agent_results, followup_results)
    all_findings = _collect_all_findings(agent_results, followup_results)

    findings_json = json.dumps(all_findings[:15], indent=2)
    contradictions_json = json.dumps(contradictions[:5], indent=2) if contradictions else "None"
    gaps_json = json.dumps(gaps[:5], indent=2) if gaps else "None"

    prompt = f"""You are a senior AI infrastructure analyst at SemiAnalysis writing an executive briefing.

Research query: "{query}"

Key findings from specialized agents:
{findings_json}

Contradictions detected:
{contradictions_json}

Information gaps:
{gaps_json}

Write a structured briefing. Return ONLY a JSON object:
{{
  "executive_summary": "2-3 sentence high-level summary",
  "direct_answer": "Clear, specific answer to the user's question with concrete numbers and timelines",
  "open_questions": ["List of 3-5 remaining questions"],
  "next_steps": ["4 recommended next research or action steps"],
  "spoken_summary": "A concise 2-3 sentence version suitable for reading aloud via TTS"
}}"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    result = json.loads(response.choices[0].message.content)

    # Merge LLM output with structured data
    result["key_findings"] = all_findings
    result["evidence_table"] = all_findings
    result["contradictions_section"] = contradictions
    result["sources"] = sources
    if "open_questions" not in result:
        result["open_questions"] = []
    if "next_steps" not in result:
        result["next_steps"] = []
    return result
