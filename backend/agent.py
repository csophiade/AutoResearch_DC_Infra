import json
import time
from typing import Generator, Dict, Any, List
from openai import OpenAI
from backend.config import settings
from backend.search import search_web

# MOCK DATA FOR HACKATHON DEMO MODE
# This guarantees beautiful, instant, and high-fidelity responses during live demos.
MOCK_DATABASE = {
    "texas": {
        "transcription": "What are the biggest constraints for AI data center expansion in Texas?",
        "queries": [
            "Texas grid capacity AI data centers ERCOT",
            "Data center water cooling constraints Texas",
            "Texas transmission line bottlenecks AI compute"
        ],
        "sources": [
            {"title": "ERCOT Grid Expansion Report 2026", "url": "https://www.ercot.com/news/reports/2026-grid-load", "content": "ERCOT projects AI and cryptocurrency load could reach 40GW by 2030. Current grid connection queues are backlogged by 3-5 years for large industrial consumers requesting over 100MW."},
            {"title": "Texas Water Development Board: Industrial Water Use", "url": "https://www.twdb.texas.gov/publications/reports/industrial-cooling", "content": "Evaporative cooling for data centers in North and West Texas is under intense regulatory scrutiny. Municipalities are restricting groundwater use, forcing operators to pivot to dry-cooling systems which lower power usage effectiveness (PUE) from 1.2 to 1.45 during peak summer heats."},
            {"title": "SemiAnalysis: The Permitting Bottleneck in the Lone Star State", "url": "https://www.semianalysis.com/p/texas-data-center-bottlenecks", "content": "While power in Texas is cheap due to wind and solar, transmission congestion from West Texas generation to Dallas/Fort Worth and Austin demand centers is causing massive basis price differentials. Data centers face local county zoning permits that take up to 18 months."},
            {"title": "ONCOR Electric Delivery Interconnection Outlook", "url": "https://www.oncor.com/interconnections-2026", "content": "ONCOR reports substation equipment lead times, specifically for 345kV autotransformers, have ballooned to 110-140 weeks, becoming a critical bottleneck for new builds."}
        ],
        "claims": [
            {"claim": "ERCOT projects AI and crypto load to hit 40GW by 2030.", "source": "ERCOT Grid Expansion Report 2026", "type": "Metric"},
            {"claim": "Substation equipment like 345kV autotransformers has lead times of 110-140 weeks.", "source": "ONCOR Electric Delivery Interconnection Outlook", "type": "Bottleneck"},
            {"claim": "Grid connection queue backlog is 3-5 years for loads over 100MW.", "source": "ERCOT Grid Expansion Report 2026", "type": "Bottleneck"},
            {"claim": "Dry-cooling systems increase peak PUE from 1.2 to 1.45 in Texas summer heat.", "source": "Texas Water Development Board: Industrial Water Use", "type": "Metric"}
        ],
        "verification": {
            "conflicts": [],
            "uncertainties": [
                "The 40GW ERCOT projection is an aggressive estimate that combines crypto mining with hyperscale AI data centers; exact division remains uncertain."
            ]
        },
        "briefing": """# Executive Briefing: AI Data Center Constraints in Texas

Texas has emerged as a premier destination for AI data center development due to abundant land and cheap renewable energy. However, the state faces severe, compounding infrastructure headwinds that threaten expansion timelines.

## 1. Transmission and Grid Connection Queues
While power generation is plentiful, interconnecting to the **ERCOT grid** has become a multi-year ordeal. Projects requiring more than 100MW face grid connection backlogs of **3 to 5 years** [1]. Furthermore, critical substation components—specifically **345kV autotransformers**—have lead times of **110 to 140 weeks** [4], delaying actual power delivery long after paper approvals are secured.

## 2. Transmission Congestion (Basis Risk)
Cheap wind and solar generation is concentrated in West Texas, whereas the primary data center clusters are in Dallas-Fort Worth, Austin, and San Antonio. This physical separation causes transmission bottlenecks. Developers face significant basis price differentials and localized county zoning delays of up to **18 months** [3].

## 3. Water Scarcity and Cooling Efficiency
Traditional evaporative cooling, which consumes millions of gallons of water daily, is facing intense regulatory pushback [2]. Municipalities are restricting groundwater access. To adapt, operators are forced to deploy **closed-loop dry-cooling systems**. While environmentally friendly, dry-cooling degrades data center efficiency, inflating the Power Usage Effectiveness (PUE) from a sleek **1.2 to 1.45** during extreme Texas summer peaks, which in turn demands more electricity [2].

## Summary Recommendation
Hyperscalers must secure equipment (transformers, generators) *before* site acquisition and design facilities directly for dry-cooling to navigate regulatory and supply chain constraints.
"""
    },
    "gpu": {
        "transcription": "Compare the latest GPUs for inference-heavy workloads.",
        "queries": [
            "Nvidia H200 vs Blackwell B200 inference benchmarks",
            "AMD Instinct MI300X LLM inference throughput cost",
            "ASICs TPU v5p vs GPUs for inference-heavy workloads"
        ],
        "sources": [
            {"title": "Nvidia Blackwell Architecture Technical Briefing", "url": "https://www.nvidia.com/en-us/data-center/blackwell", "content": "Blackwell B200 delivers up to 30x faster LLM inference performance compared to Hopper H100 by utilizing a second-generation transformer engine supporting FP4 precision and 20 PFLOPS of compute."},
            {"title": "AMD Instinct MI300X Benchmark Analysis", "url": "https://www.amd.com/en/products/accelerators/instinct/mi300x", "content": "MI300X features 192GB of HBM3 memory with 5.3 TB/s bandwidth. For high-concurrency LLM inference (e.g. Llama 3 70B), the massive memory capacity allows hosting larger models on a single GPU, reducing networking overhead."},
            {"title": "Google Cloud TPU v5e and v5p Pricing and Performance", "url": "https://cloud.google.com/tpu/docs/v5p-performance", "content": "TPU v5p provides 459 TFLOPS of BF16 compute and 95GB HBM2e memory. While highly optimized for internal Google models, it shows lower flexibility for custom open-source model topologies compared to NVIDIA GPUs."}
        ],
        "claims": [
            {"claim": "NVIDIA Blackwell B200 delivers up to 30x faster LLM inference than H100 using FP4 precision.", "source": "Nvidia Blackwell Architecture Technical Briefing", "type": "Performance"},
            {"claim": "AMD MI300X has 192GB HBM3 memory and 5.3 TB/s bandwidth.", "source": "AMD Instinct MI300X Benchmark Analysis", "type": "Specs"},
            {"claim": "Google TPU v5p provides 459 TFLOPS BF16 and 95GB HBM2e.", "source": "Google Cloud TPU v5e and v5p Pricing and Performance", "type": "Specs"}
        ],
        "verification": {
            "conflicts": [
                {"fact_a": "Nvidia claims 30x speedup over H100.", "fact_b": "Real-world tests show typical speedups of 3x-8x depending on batch sizes and precision mapping.", "explanation": "The 30x speedup claim relies on FP4 precision and mixture-of-experts model optimizations, which are not universally applicable."}
            ],
            "uncertainties": ["FP4 software maturity and quantization loss for production-grade models is still under active evaluation."]
        },
        "briefing": """# Executive Briefing: GPUs & Accelerators for Inference-Heavy Workloads

Inference is fast overtaking training as the primary driver of AI compute spend. Choosing an accelerator involves balancing memory bandwidth, software optimization, and hardware availability.

## 1. NVIDIA Blackwell (B200/B100) vs. Hopper (H200/H100)
NVIDIA’s Blackwell architecture represents a paradigm shift by natively supporting **FP4 precision** via its 2nd-gen Transformer Engine. NVIDIA claims up to a **30x throughput increase** over H100 for LLM inference [1]. However, real-world benchmarks show that typical gains are closer to **3x to 8x** unless the model is specifically optimized for FP4 [1]. The **H200** remains the immediate pragmatic choice, featuring **141GB HBM3e** memory which resolves the memory capacity bottleneck of the original H100.

## 2. AMD Instinct MI300X: The Memory Kingpin
For hosting large open-source LLMs (like Llama-3 70B/405B) at high concurrency, the **AMD MI300X** is a formidable challenger. It boasts **192GB of HBM3 memory** and **5.3 TB/s of bandwidth** [2]. This massive capacity allows developers to run larger models on fewer chips, drastically reducing inter-GPU communication bottlenecks and lowering total cost of ownership (TCO) for inference clusters.

## 3. Google TPU v5p: The Hyperscale Alternative
For teams deeply integrated into the Google Cloud ecosystem, the **TPU v5p** offers high-performance BF16 compute (459 TFLOPS) and **95GB HBM2e memory** [3]. TPUs offer excellent price-to-performance for standard architectures, though they lack the general-purpose software flexibility and ecosystem support that NVIDIA’s CUDA environment provides [3].

## Summary Recommendation
For ultra-low latency and cutting-edge FP4 optimization, Blackwell is unmatched. For cost-effective open-source hosting at scale with high concurrency, AMD's MI300X offers superior memory economics.
"""
    },
    "companies": {
        "transcription": "Which companies are expanding AI compute capacity fastest?",
        "queries": [
            "Hyperscaler capital expenditure AI data centers 2026",
            "Meta Microsoft Google Oracle AI cluster sizes",
            "Data center builders capacity expansion metrics"
        ],
        "sources": [
            {"title": "Synergy Research Group: Q1 2026 Cloud Spend Analysis", "url": "https://www.srgresearch.com/articles/q1-2026-hyperscale-capex", "content": "Microsoft and Meta led hyperscale capital expenditures, with Microsoft's quarterly capex breaching $14 billion, primarily directed to AI hardware and leased data center facilities. Oracle expanded its cloud footprint by 85% year-over-year."},
            {"title": "SemiAnalysis: AI Cluster Trackers and Power Pipelines", "url": "https://www.semianalysis.com/p/ai-cluster-tracker-2026", "content": "Microsoft is constructing a 100,000 GPU cluster in Wisconsin and planning a multi-gigawatt Stargate system with OpenAI. Meta has deployed over 350,000 H100-equivalents and is actively acquiring capacity in secondary markets."},
            {"title": "CoreWeave and Lambda Labs Debt Financing Press Releases", "url": "https://www.coreweave.com/news/series-d-debt-financing", "content": "Specialty GPU clouds like CoreWeave secured an additional $7.5 billion in debt financing to purchase Blackwell systems, expanding their footprint from 14 to 28 data centers globally."}
        ],
        "claims": [
            {"claim": "Microsoft quarterly capex exceeded $14 billion, targeting AI infra.", "source": "Synergy Research Group: Q1 2026 Cloud Spend Analysis", "type": "Metric"},
            {"claim": "Oracle cloud footprint expanded by 85% year-over-year.", "source": "Synergy Research Group: Q1 2026 Cloud Spend Analysis", "type": "Metric"},
            {"claim": "CoreWeave secured $7.5 billion in debt to expand from 14 to 28 data centers.", "source": "CoreWeave and Lambda Labs Debt Financing Press Releases", "type": "Expansion"}
        ],
        "verification": {
            "conflicts": [],
            "uncertainties": [
                "Hyperscalers report total Capex, which includes land, building shells, and server silicon; the exact allocation specifically to GPU silicon is estimated, not officially disclosed."
            ]
        },
        "briefing": """# Executive Briefing: Leading Companies Expanding AI Compute

The race for AI supremacy has triggered an unprecedented surge in physical infrastructure capital expenditure. Expansion is dominated by traditional hyperscalers and heavily funded specialized cloud providers.

## 1. Microsoft and OpenAI (The Giants)
Microsoft continues to expand compute capacity faster than any other entity. Its quarterly capital expenditure has surpassed **$14 billion**, with the majority funnelled into AI servers and data center leases [1]. Microsoft is currently building a massive **100,000-GPU cluster** in Wisconsin and collaborating with OpenAI on the multi-gigawatt, multi-billion-dollar **"Stargate"** data center project [2].

## 2. Meta (The Open-Source Champion)
Meta is expanding capacity at an aggressive rate to support its Llama models. Meta has deployed over **350,000 H100-equivalent GPUs** [2]. Unlike Microsoft, which relies heavily on third-party colocation operators, Meta is redesigning and building its own custom data centers optimized for liquid-cooled, high-density AI clusters.

## 3. Oracle and Specialized Clouds (CoreWeave, Lambda)
* **Oracle** is growing faster in percentage terms than AWS or Google, expanding its cloud infrastructure footprint by **85% year-over-year** [1].
* **CoreWeave** has secured a massive **$7.5 billion in debt financing** [3] to fund the purchase of NVIDIA Blackwell chips. This capital will double their footprint from **14 to 28 data centers** globally [3], making them one of the fastest-growing physical compute operators in the world.

## Summary Recommendation
Microsoft and Meta remain the largest absolute buyers of compute, while Oracle and CoreWeave represent the fastest-growing cloud alternatives for enterprise workloads.
"""
    },
    "bottlenecks": {
        "transcription": "What are the current bottlenecks in AI infrastructure: chips, power, cooling, networking, or real estate?",
        "queries": [
            "AI data center bottlenecks power vs cooling vs chips 2026",
            "High-density cooling liquid cooling supply chain lead times",
            "Data center fiber networking switches optic transceivers shortage"
        ],
        "sources": [
            {"title": "U.S. Department of Energy: Grid Capacity and Data Centers", "url": "https://www.energy.gov/policy/grid-capacity-data-centers-2026", "content": "Power availability has surpassed chip supply as the #1 bottleneck. The backlog to upgrade transmission lines and connect new high-voltage substations ranges from 4 to 7 years in major markets like Northern Virginia."},
            {"title": "Vertiv Q1 2026 Earnings Call Transcript", "url": "https://investors.vertiv.com/q1-2026-results", "content": "Demand for liquid cooling (direct-to-chip and rear-door heat exchangers) has tripled. Lead times for coolant distribution units (CDUs) and chillers are sitting at 60-80 weeks due to pump and manifold shortages."},
            {"title": "Crehan Research: High-Speed Networking and Optics", "url": "https://www.crehanresearch.com/reports/networking-optics-leadtimes", "content": "Transition to 800G and 1.6T networking has caused a shortage in high-speed optical transceivers. Current lead times for optical switches stand at 45 weeks."}
        ],
        "claims": [
            {"claim": "Grid connection backlog for transmission lines ranges from 4 to 7 years in major markets.", "source": "U.S. Department of Energy: Grid Capacity and Data Centers", "type": "Bottleneck"},
            {"claim": "Lead times for CDUs and liquid cooling equipment are 60-80 weeks.", "source": "Vertiv Q1 2026 Earnings Call Transcript", "type": "Bottleneck"},
            {"claim": "High-speed optical switches have lead times of 45 weeks.", "source": "Crehan Research: High-Speed Networking and Optics", "type": "Bottleneck"}
        ],
        "verification": {
            "conflicts": [],
            "uncertainties": [
                "While power is the absolute bottleneck in Tier-1 markets (Northern Virginia, Silicon Valley), secondary markets (Ohio, Georgia) still have available power but suffer from local municipal permitting delays."
            ]
        },
        "briefing": """# Executive Briefing: Bottlenecks in AI Infrastructure

As GPU supply constraints ease compared to the peak shortages of 2023-2024, physical infrastructure has become the primary gating factor for the deployment of AI compute.

## 1. Power and Grid Connections (The Primary Constraint)
Power availability is currently the **#1 bottleneck** in AI infrastructure. In key markets like Northern Virginia (PJM), connecting a new high-voltage substation can take **4 to 7 years** [1]. The grid simply lacks the transmission capacity to move power from generation sites to high-density data center hubs, forcing developers to look at secondary markets.

## 2. Liquid Cooling Equipment (Thermal Constraint)
Modern GPUs (like Nvidia Blackwell B200) dissipate over 1,000W per chip, requiring **direct-to-chip liquid cooling**. The supply chain for thermal management is severely stressed. Lead times for **Coolant Distribution Units (CDUs)** and specialized chillers have reached **60 to 80 weeks** due to shortages in precision valves, pumps, and manifolds [2].

## 3. High-Speed Networking and Optics
To connect thousands of GPUs in a single cluster, ultra-low latency networking is required. The industry transition to **800G and 1.6T speeds** has caused shortages in optical transceivers and switches. Lead times for high-speed networking switches currently sit at **45 weeks** [3].

## Summary Recommendation
AI builders must pivot from 'just-in-time' procurement to a 'just-in-case' strategy, pre-ordering long-lead equipment (cooling, switches, transformers) up to two years in advance of site construction.
"""
    },
    "deals": {
        "transcription": "Research recent data center deals and summarize the implications for hyperscalers.",
        "queries": [
            "Recent hyperscaler data center lease acquisitions 2026",
            "Blackstone QTS data center deals AI pipelines",
            "Digital Realty Equinix joint ventures hyperscale"
        ],
        "sources": [
            {"title": "Blackstone Real Estate Data Center Strategy Update", "url": "https://www.blackstone.com/news/press-releases/qts-infrastructure-deal-2026", "content": "Blackstone's QTS has signed over $15 billion in leasing deals with hyperscalers in the first half of 2026. These lease agreements are typically 10-15 year terms with escalators, locking in capacity in primary power zones."},
            {"title": "Digital Realty and Blackstone Joint Venture Press Release", "url": "https://www.digitalrealty.com/news/blackstone-joint-venture-7gb-portfolio", "content": "Digital Realty closed a joint venture with Blackstone to develop $7 billion worth of hyperscale data centers across Frankfurt, Paris, and Northern Virginia, pre-leased to anchor cloud clients."},
            {"title": "SemiAnalysis: Capitalizing on the Land Grab", "url": "https://www.semianalysis.com/p/data-center-leases-2026", "content": "Hyperscalers are signing 'powered shell' leases at double the historical lease rate ($150-$180/kW/month) just to secure grid allocation. This increases capital efficiency for developers but locks hyperscalers into expensive long-term operating lease liabilities."}
        ],
        "claims": [
            {"claim": "QTS (Blackstone) signed over $15 billion in leases with hyperscalers in H1 2026.", "source": "Blackstone Real Estate Data Center Strategy Update", "type": "Deals"},
            {"claim": "Digital Realty and Blackstone formed a $7 billion JV for hyperscale sites.", "source": "Digital Realty and Blackstone Joint Venture Press Release", "type": "Deals"},
            {"claim": "Powered shell leases are reaching premium rates of $150-$180 per kW per month.", "source": "SemiAnalysis: Capitalizing on the Land Grab", "type": "Cost"}
        ],
        "verification": {
            "conflicts": [],
            "uncertainties": [
                "The exact identities of the hyperscalers leasing QTS facilities are protected by strict NDAs, though analysts agree they are primarily Microsoft, Meta, and Google."
            ]
        },
        "briefing": """# Executive Briefing: Recent Data Center Deals & Hyperscale Implications

The physical real estate and power grid allocation for AI compute has turned into a massive land grab. Recent multi-billion-dollar deals show structural changes in how data centers are funded and leased.

## 1. Blackstone & QTS Domination
Blackstone’s QTS has emerged as a powerhouse, signing a staggering **$15 billion in leasing agreements** with hyperscalers in the first half of 2026 [1]. By purchasing massive tracts of land with pre-negotiated power rights over the past five years, QTS is one of the few builders capable of delivering 100MW+ campuses immediately.

## 2. Megawatt Joint Ventures
To fund the massive capital demands of AI construction, colocation providers are partnering with private equity. **Digital Realty** and **Blackstone** closed a **$7 billion joint venture** to build campuses in Frankfurt, Paris, and Northern Virginia [2]. This allows developers to construct facilities without overloading their balance sheets, relying on private credit to fund the build.

## 3. Premium Pricing and Financial Liabilities
Due to the shortage of power, lease pricing has skyrocketed. Hyperscalers are paying premium rates of **$150 to $180 per kW per month** for 'powered shells' (empty buildings with grid connections but no servers or cooling installed) [3]. This represents double the historical rate, significantly increasing the long-term fixed operating lease liabilities for companies like Microsoft, Google, and Meta.

## Summary Recommendation
Hyperscalers are locking in capacity at peak prices. If LLM training and inference efficiency improves drastically or demand softens, these long-term lease liabilities could become significant financial weights.
"""
    }
}


def _detect_closest_mock_key(query: str) -> str:
    """
    Analyzes the query and returns 'texas', 'gpu', 'companies', 'bottlenecks', 'deals',
    or 'generic' if none match.
    """
    q = query.lower()
    if "texas" in q or "ercot" in q:
        return "texas"
    elif "gpu" in q or "inference" in q or "nvidia" in q or "amd" in q:
        return "gpu"
    elif "companies" in q or "expanding" in q or "capex" in q or "coreweave" in q:
        return "companies"
    elif "bottleneck" in q or "constraint" in q or "power" in q or "cooling" in q or "real estate" in q:
        return "bottlenecks"
    elif "deal" in q or "lease" in q or "blackstone" in q or "qts" in q or "digital realty" in q:
        return "deals"
    return "generic"


def _generate_generic_mock(query: str) -> Dict[str, Any]:
    """Generates a structured, realistic mock response for any arbitrary user query."""
    return {
        "transcription": query,
        "queries": [
            f"AI infrastructure trends related to {query}",
            f"Supply chain implications of {query}",
            f"Market analyst perspective on {query}"
        ],
        "sources": [
            {"title": "Gartner Emerging Infrastructure Report 2026", "url": "https://www.gartner.com/trends/infrastructure-2026", "content": f"The rapid expansion of AI compute has forced an evaluation of {query}. Organizations are focusing on capital efficiency and time-to-market."},
            {"title": "SemiAnalysis AI Outlook 2026", "url": "https://www.semianalysis.com/outlook-2026", "content": f"Analyzing the supply-demand curves for {query} indicates structural bottlenecks. Leading players are locking in long-term supplier agreements."}
        ],
        "claims": [
            {"claim": f"Supply-demand curves for {query} indicate impending structural constraints.", "source": "SemiAnalysis AI Outlook 2026", "type": "Analysis"},
            {"claim": f"Time-to-market is the primary metric for organizations evaluating {query}.", "source": "Gartner Emerging Infrastructure Report 2026", "type": "Strategy"}
        ],
        "verification": {
            "conflicts": [],
            "uncertainties": [f"Long-term adoption rate and demand elasticity for {query} remains highly variable depending on macroeconomic factors."]
        },
        "briefing": f"""# Executive Briefing: Analysis of {query}

This briefing reviews the infrastructure implications, market dynamics, and strategic recommendations regarding the query: "{query}".

## 1. Supply Chain and Constraints
Analysis of the current supply curves indicates that operators evaluating this space face localized bottlenecks [2]. Organizations that prioritize early capital allocation and long-term supplier agreements are achieving significantly faster time-to-market than competitors who rely on standard spot markets [1].

## 2. Strategic Tradeoffs
Operational capacity is currently constrained by physical infrastructure delivery rates rather than raw demand. As a result, companies are accepting premium pricing structures in primary hubs to lock in critical resources [2].

## Summary Recommendation
Decision-makers should secure long-term capacity reservations immediately, diversifying across geographic regions to hedge against localized grid and regulatory bottlenecks.
"""
    }


def run_mock_pipeline(query: str) -> Generator[Dict[str, Any], None, None]:
    """
    Executes a simulated, highly interactive research pipeline.
    Yields step-by-step progress reports to feed the frontend's SSE log.
    """
    key = _detect_closest_mock_key(query)
    data = MOCK_DATABASE[key] if key in MOCK_DATABASE else _generate_generic_mock(query)
    
    # Step 1: Planning
    yield {"step": "plan", "message": "Planner: Decomposing research request into sub-queries...", "data": None}
    time.sleep(1.0)
    yield {"step": "plan", "message": f"Planner formulated search queries:\n" + "\n".join([f"  • {q}" for q in data["queries"]]), "data": data["queries"]}
    
    # Step 2: Search
    yield {"step": "search", "message": "Search: Retrieving documents from web, trade journals, and financial reports...", "data": None}
    time.sleep(1.2)
    sources_summary = "\n".join([f"  • [{i+1}] {s['title']} ({s['url']})" for i, s in enumerate(data["sources"])])
    yield {"step": "search", "message": f"Search gathered {len(data['sources'])} sources:\n{sources_summary}", "data": data["sources"]}
    
    # Step 3: Extraction
    yield {"step": "extract", "message": "Extraction: Parsing text and extracting hard claims, metrics, and bottlenecks...", "data": None}
    time.sleep(1.0)
    claims_summary = "\n".join([f"  • Extracted [{c['type']}]: '{c['claim']}' (Source: {c['source']})" for c in data["claims"]])
    yield {"step": "extract", "message": f"Extraction complete. Found {len(data['claims'])} primary claims:\n{claims_summary}", "data": data["claims"]}
    
    # Step 4: Verification
    yield {"step": "verify", "message": "Verification: Auditing claims for inconsistencies, conflicts, or gaps...", "data": None}
    time.sleep(1.0)
    
    v_data = data["verification"]
    if v_data.get("conflicts"):
        conf_summary = "\n".join([f"  ⚠️ Conflict: {c['explanation']}\n    - Claim A: {c['fact_a']}\n    - Claim B: {c['fact_b']}" for c in v_data["conflicts"]])
        yield {"step": "verify", "message": f"Verification found conflicts:\n{conf_summary}", "data": v_data}
    else:
        yield {"step": "verify", "message": "Verification: All claims cross-referenced. No direct contradictions found. Core datasets are consistent.", "data": v_data}
        
    if v_data.get("uncertainties"):
        unc_summary = "\n".join([f"  • Uncertainty: {u}" for u in v_data["uncertainties"]])
        yield {"step": "verify", "message": f"Uncertainties/Gaps flagged:\n{unc_summary}", "data": v_data}
        
    time.sleep(0.8)
    
    # Step 5: Synthesis
    yield {"step": "synthesize", "message": "Synthesis: Compiling formal executive briefing and applying citations...", "data": None}
    time.sleep(1.2)
    
    final_output = {
        "briefing": data["briefing"],
        "sources": data["sources"]
    }
    yield {"step": "completed", "message": "Autonomous research pipeline complete. Summary drafted.", "data": final_output}


# PRODUCTION LLM-BASED PIPELINE RUNNER
def run_production_pipeline(query: str, openai_client: OpenAI) -> Generator[Dict[str, Any], None, None]:
    """
    Executes a real-time LLM agent loop:
    1. Planner: LLM decomposes query -> 3 search queries
    2. Searcher: Searches web using Tavily/DuckDuckGo
    3. Extractor: LLM pulls claims from search page contents
    4. Verifier: LLM checks consistency & flags gaps
    5. Synthesizer: LLM writes final report
    """
    try:
        # Step 1: Planner
        yield {"step": "plan", "message": "Planner: Decomposing research request into search queries...", "data": None}
        
        planner_prompt = f"""
        You are an elite research planner for AI infrastructure.
        Decompose this user query into 3 specific, distinct search queries that would help gather data.
        User Query: "{query}"
        
        Return ONLY a JSON object in this format:
        {{
            "queries": ["query 1", "query 2", "query 3"]
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": planner_prompt}],
            response_format={"type": "json_object"}
        )
        
        plan_data = json.loads(response.choices[0].message.content)
        queries = plan_data.get("queries", [query])
        
        yield {"step": "plan", "message": f"Planner formulated search queries:\n" + "\n".join([f"  • {q}" for q in queries]), "data": queries}
        
        # Step 2: Search
        yield {"step": "search", "message": "Search: Querying web endpoints...", "data": None}
        
        all_sources = []
        seen_urls = set()
        
        for q in queries:
            results = search_web(q, max_results=3)
            for res in results:
                url = res.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_sources.append(res)
                    
        sources_summary = "\n".join([f"  • [{i+1}] {s['title']} ({s['url']})" for i, s in enumerate(all_sources)])
        yield {"step": "search", "message": f"Search gathered {len(all_sources)} unique sources:\n{sources_summary}", "data": all_sources}
        
        if not all_sources:
            yield {"step": "search", "message": "⚠️ Warning: Search gathered zero results. Pipeline will proceed with empty context.", "data": []}

        # Step 3: Extraction
        yield {"step": "extract", "message": "Extraction: Analyzing page snippets and extracting core facts...", "data": None}
        
        context_str = ""
        for i, src in enumerate(all_sources):
            context_str += f"Source [{i+1}]: {src['title']}\nURL: {src['url']}\nSnippet: {src['content']}\n\n"
            
        extraction_prompt = f"""
        You are an expert infrastructure analyst. Extract key claims, numbers, statistics, companies, locations, dates, and bottlenecks from the following source materials.
        
        Sources:
        {context_str}
        
        Return ONLY a JSON object in this format:
        {{
            "claims": [
                {{
                    "claim": "Specific factual claim with numbers/details",
                    "source": "Title of the source",
                    "type": "Metric/Bottleneck/Expansion/Deal"
                }}
            ]
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extraction_prompt}],
            response_format={"type": "json_object"}
        )
        
        claims_data = json.loads(response.choices[0].message.content)
        claims = claims_data.get("claims", [])
        
        claims_summary = "\n".join([f"  • Extracted [{c.get('type', 'Factual')}]: '{c.get('claim')}' (Source: {c.get('source')})" for c in claims])
        yield {"step": "extract", "message": f"Extraction complete. Found {len(claims)} primary claims:\n{claims_summary}", "data": claims}
        
        # Step 4: Verification
        yield {"step": "verify", "message": "Verification: Auditing claims for contradictions and gaps...", "data": None}
        
        claims_str = json.dumps(claims, indent=2)
        verification_prompt = f"""
        You are an auditor verifying claims made by different sources. Review these extracted claims:
        {claims_str}
        
        Identify:
        1. Any direct conflicts or contradictions (e.g. conflicting dates, capacity numbers, or timelines).
        2. Key gaps or uncertainties that are unaddressed by these claims.
        
        Return ONLY a JSON object in this format:
        {{
            "conflicts": [
                {{
                    "fact_a": "Claim A",
                    "fact_b": "Claim B",
                    "explanation": "Why they contradict or differ"
                }}
            ],
            "uncertainties": [
                "Uncertainty description or missing information"
            ]
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": verification_prompt}],
            response_format={"type": "json_object"}
        )
        
        verification_data = json.loads(response.choices[0].message.content)
        conflicts = verification_data.get("conflicts", [])
        uncertainties = verification_data.get("uncertainties", [])
        
        if conflicts:
            conf_summary = "\n".join([f"  ⚠️ Conflict: {c['explanation']}\n    - Claim A: {c['fact_a']}\n    - Claim B: {c['fact_b']}" for c in conflicts])
            yield {"step": "verify", "message": f"Verification flagged conflicts:\n{conf_summary}", "data": verification_data}
        else:
            yield {"step": "verify", "message": "Verification: No direct contradictions or naming discrepancies found across sources.", "data": verification_data}
            
        if uncertainties:
            unc_summary = "\n".join([f"  • Uncertainty: {u}" for u in uncertainties])
            yield {"step": "verify", "message": f"Uncertainties/Gaps flagged:\n{unc_summary}", "data": verification_data}
            
        # Step 5: Synthesis
        yield {"step": "synthesize", "message": "Synthesis: Compiling formal executive briefing and applying citations...", "data": None}
        
        synthesis_prompt = f"""
        You are the lead analyst at SemiAnalysis. Write an elite, professional executive briefing on: "{query}"
        
        Utilize the following sources and context:
        {context_str}
        
        Extracted claims context:
        {claims_str}
        
        Verification audit results (make sure to call out these conflicts/gaps if relevant):
        {json.dumps(verification_data, indent=2)}
        
        Formatting Requirements:
        - Write in markdown with headers, bullet points, and strong emphasis.
        - Cite your facts using brackets corresponding to the source number, e.g. [1], [2], etc.
        - Be authoritative, specific, and metric-focused (use numbers, power loads, dollar values).
        - Limit the final briefing to 350-450 words so that it remains readable and easy to read aloud in the demo.
        - Structure:
          # Title
          Brief intro
          ## 1. Section One (e.g. Power, Hardware, capacity etc.)
          ## 2. Section Two
          ## 3. Section Three
          ## Summary Recommendation
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.7
        )
        
        briefing = response.choices[0].message.content
        
        final_output = {
            "briefing": briefing,
            "sources": all_sources
        }
        yield {"step": "completed", "message": "Autonomous research pipeline complete. Summary drafted.", "data": final_output}
        
    except Exception as e:
        yield {"step": "error", "message": f"Pipeline failure: {str(e)}. Falling back to mock response.", "data": None}
        # Run mock fallback
        for event in run_mock_pipeline(query):
            yield event
