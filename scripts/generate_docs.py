#!/usr/bin/env python3
"""
Generates the canonical docs/index.md page for Model v3.0.
- Decouples presentation styles from ontology (snake_case NodeKindEnum to Mermaid shapes)
- Renders full unified Mermaid ecosystem diagram with adversaries & algedonic signals
- Renders tables for Wardley Stages, Named Feedback Loops, and Viewpoint-Relative VSM Frames
"""

import sys
import yaml
import html
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTRO_TEMPLATE = PROJECT_ROOT / "templates" / "model_introduction.md"
MODEL_FILE = PROJECT_ROOT / "model" / "ai_ecosystem.yaml"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "index.md"

KIND_TO_SHAPE = {
    "statutory_authority":   "hexagon",
    "public_authority":      "hexagon",
    "private_oversight_body":"stadium",
    "organisation":          "rect",
    "person":                "circle",
    "threat_actor":          "hexagon",
    "software_service":      "rounded",
    "control_component":     "subproc",
    "data_store":            "cylinder",
    "commons":               "stadium",
}

def format_node_shape(node_id, label, sublabel, kind):
    shape = KIND_TO_SHAPE.get(kind, "rect")
    sub = f"<br/><small><i>{html.escape(sublabel)}</i></small>" if sublabel else ""
    content = f'"{html.escape(label)}{sub}"'
    
    if shape == "hexagon": return f"{node_id}{{{{{content}}}}}"
    elif shape == "cylinder": return f"{node_id}[({content})]"
    elif shape == "subproc": return f"{node_id}[[{content}]]"
    elif shape == "stadium": return f"{node_id}([{content}])"
    elif shape == "circle": return f"{node_id}(({content}))"
    elif shape == "rounded": return f"{node_id}({content})"
    return f"{node_id}[{content}]"

def edge_to_mermaid(e):
    rkind = e.get("relation_kind", "data_flow")
    label = e.get("label", "").replace('"', "'")
    if rkind == "algedonic_signal":
        return f'== "🚨 {label}" ==>'
    elif rkind in ["commercial_flow", "resource_supply", "statutory_mandate"]:
        return f'== "{label}" ==>'
    elif rkind in ["liability_exposure", "contractual_term", "governance_control", "competitive_pressure", "physical_constraint"]:
        return f'-. "{label}" .->'
    elif rkind == "adversarial_attack":
        return f'-. "⚡ {label}" .->'
    return f'-->|"{label}"|'

def get_node_class(node):
    domains = node.get("domains", [])
    if node.get("kind") == "threat_actor": return "gov"
    if "governance" in domains: return "gov"
    if "economic" in domains: return "econ"
    if "technical" in domains: return "tech"
    return "default"

def build_visual_key_mermaid():
    lines = [
        "flowchart LR",
        "    classDef gov fill:#FFF1F0,stroke:#F5222D,stroke-width:2px;",
        "    classDef econ fill:#F6FFED,stroke:#52C41A,stroke-width:2px;",
        "    classDef tech fill:#E6F7FF,stroke:#1890FF,stroke-width:2px;",
        "    classDef default fill:#F8FAFC,stroke:#64748B,stroke-width:1.5px;",
        "",
        '    subgraph LegendShapes ["Architectural Node Archetypes"]'
    ]
    key_samples = [
        ("K_STA", "Statutory Authority", "statutory_authority", "gov"),
        ("K_PUB", "Public Authority (AISI)", "public_authority", "gov"),
        ("K_PRV", "Private Oversight Body", "private_oversight_body", "gov"),
        ("K_ORG", "Organisation", "organisation", "econ"),
        ("K_PER", "Person", "person", "gov"),
        ("K_THR", "Threat Actor", "threat_actor", "gov"),
        ("K_SWS", "Software Service", "software_service", "tech"),
        ("K_CTR", "Control Component", "control_component", "tech"),
        ("K_STO", "Data Store", "data_store", "tech"),
        ("K_COM", "Commons", "commons", "tech"),
    ]
    for nid, lbl, kind, cls in key_samples:
        rendered = format_node_shape(nid, lbl, f"kind: {kind}", kind)
        lines.append(f"        {rendered}:::{cls}")
    lines.append("    end")
    return "\n".join(lines)

def build_notation_table():
    return """### Node Archetypes (Kinds)

| Kind | Semantic Meaning | Visual Shape |
| :--- | :--- | :---: |
| `statutory_authority` | Legal authorities, enforcement agencies, courts, market surveillance | `hexagon` |
| `public_authority` | Non-statutory public bodies: national AI safety institutes, horizon evaluators | `hexagon` |
| `private_oversight_body` | Standards bodies, accredited certification and audit bodies (ISO/CEN) | `stadium` |
| `organisation` | Commercial firms, labs, cloud platforms, deployers, insurers, capital funds | `rect` |
| `person` | Natural persons or populations (delegators, overseers, citizens, consumers) | `circle` |
| `threat_actor` | Hostile adversaries (prompt injectors, jailbreakers, model poisoners) | `hexagon` |
| `software_service` | Models, vertical applications, agent runtimes, observability engines | `rounded` |
| `control_component` | Deterministic gates, policy kernels, identity brokers, tool gateways | `subproc` |
| `data_store` | Vector knowledge bases, sovereign audit ledgers, production ERP systems | `cylinder` |
| `commons` | Open-weight model weights, open-source codebases, shared artifacts | `stadium` |

### Relationship & Edge Types

| Line Style | Semantic Relation Kind | Description |
| :---: | :--- | :--- |
| `== '🚨 label' ==>` | `algedonic_signal` | **VSM Emergency Tripwire:** Direct crisis bypass from S1 operations to S5 board/policy |
| `== 'label' ==>` | `commercial_flow` | Capital investment, SaaS fees, wholesale token tolls, insurance premiums |
| `== 'label' ==>` | `resource_supply` | Hardware allocation, compute capacity delivery, training data corpus |
| `== 'label' ==>` | `statutory_mandate` | Statutory orders, compliance mandates, export control sanctions |
| `-. 'label' .->` | `governance_control` | Policy bounds, audit trail logging, S3* independent sampling probes |
| `-. 'label' .->` | `liability_exposure` | Real-world tort liability, blast radius causation, direct civil exposure |
| `-. 'label' .->` | `competitive_pressure` | Market margin compression, platform absorption, open-weight price deflation |
| `-. 'label' .->` | `physical_constraint` | Hard physical limits: power grid capacity, transformer delays, fab throughput |
| `-. '⚡ label' .->` | `adversarial_attack` | Hostile prompt injection, jailbreaking, data poisoning, credential theft |
| `-. 'label' .->` | `contractual_term` | Contractual liability carve-outs, ToS 'AS-IS' disclaimers |
| `-->|'label'|` | `protocol_call` | Technical protocols (A2E, MIP, A2T via MCP, A2A) |
| `-->|'label'|` | `data_flow` | Telemetry traces, prompt context (RAG), model weights, evidence logs |

### Market Dynamics: Wardley Stages, Power Asymmetry & Switching Costs

| Property | Values | Semantic Meaning |
| :--- | :--- | :--- |
| **`evolution_stage`** | `genesis` | Novel, experimental, unproven concepts with high uncertainty |
| | `custom_built` | Bespoke, differentiated implementations or rare capital assets (e.g. ASML lithography) |
| | `product` | Standardized, commercially packaged software or hardware products |
| | `commodity` | Ubiquitous utility or open commons (zero-marginal cost) |
| **`power_asymmetry`** | `supplier_dominant` | Supplier dictates pricing, access, and terms (seller's market) |
| | `buyer_dominant` | Buyer dictates terms and performance specifications (buyer's market) |
| | `balanced` | Bilateral commercial parity |
| | `captive` | Downstream participant is structurally trapped with near-zero alternative options |
| **`switching_cost`** | `prohibitive` | Switching requires full architectural, physical, or legal refactoring |
| | `high` | Switching requires extensive re-indexing, prompt re-tuning, and workflow rebuilding |
| | `moderate` | Standard multi-cloud or modular API adaptation effort |
| | `low` | Commoditized, drop-in replacement (e.g. OpenAI-compatible open-weight endpoints) |"""

def build_full_unified_mermaid(model):
    lines = [
        "flowchart TB",
        "    classDef gov fill:#FFF1F0,stroke:#F5222D,stroke-width:2px;",
        "    classDef econ fill:#F6FFED,stroke:#52C41A,stroke-width:2px;",
        "    classDef tech fill:#E6F7FF,stroke:#1890FF,stroke-width:2px;",
        "    classDef default fill:#F8FAFC,stroke:#64748B,stroke-width:1.5px;",
        ""
    ]
    clusters = {c["id"]: c for c in model.get("clusters", [])}
    nodes_by_cluster = {}
    for n in model["nodes"]:
        nodes_by_cluster.setdefault(n.get("cluster", "root"), []).append(n)
        
    for cid, nodes in nodes_by_cluster.items():
        clabel = clusters[cid]["label"] if cid in clusters else cid
        lines.append(f'    subgraph {cid} ["{clabel}"]')
        for n in nodes:
            shape_code = format_node_shape(n["id"], n["label"], n.get("sublabel", ""), n.get("kind", "organisation"))
            lines.append(f'        {shape_code}:::{get_node_class(n)}')
        lines.append("    end\n")
        
    for e in model["edges"]:
        lines.append(f'    {e["from"]} {edge_to_mermaid(e)} {e["to"]}')
        
    return "\n".join(lines)

def format_cardinality(n):
    c_min = n.get("cardinality_log10_min")
    c_max = n.get("cardinality_log10_max")
    unit = n.get("cardinality_unit", "")
    if c_min is not None and c_max is not None:
        if c_min == c_max:
            return f"10^{c_min:g} {unit}"
        return f"10^{c_min:g}–10^{c_max:g} {unit}"
    return "—"

def main():
    if not MODEL_FILE.exists():
        sys.exit(f"[ERROR] Model file not found at: {MODEL_FILE}")

    with open(MODEL_FILE, "r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    if INTRO_TEMPLATE.exists():
        intro_content = INTRO_TEMPLATE.read_text(encoding="utf-8").strip()
    else:
        intro_content = (
            "# Canonical AI Ecosystem Model\n\n"
            "A logical property graph integrating cognitive agent state (CoALA), "
            "cybernetic control (Beer's VSM), macro-economics, standards bodies, and regulatory liability."
        )

    key_chart = build_visual_key_mermaid()
    key_tables = build_notation_table()
    full_mermaid = build_full_unified_mermaid(model)

    md = [
        "---",
        "title: Canonical AI Ecosystem Model",
        "sidebar_position: 1",
        "slug: /",
        "---",
        "",
        "import useBaseUrl from '@docusaurus/useBaseUrl';",
        "",
        intro_content,
        "",
        ":::tip Download Canonical Models",
        "Download the raw model to query in external visual modeling tools:",
        "",
        '- <a href={useBaseUrl("/exports/ai_ecosystem.graphml")} download="ai_ecosystem.graphml">**Download for yEd** (.graphml)</a>',
        '- <a href={useBaseUrl("/exports/ai_ecosystem.drawio")} download="ai_ecosystem.drawio">**Download for draw.io** (.drawio)</a>',
        '- <a href={useBaseUrl("/exports/ai_ecosystem_kumu.json")} download="ai_ecosystem_kumu.json">**Download for Kumu Blueprint** (.json)</a>',
        ":::",
        "",
        "<details>",
        "<summary><strong>📖 Visual Language & Architectural Key (Click to expand)</strong></summary>",
        "",
        "```mermaid",
        key_chart,
        "```",
        "",
        key_tables,
        "",
        "</details>",
        "",
        "## Unified Ecosystem Architecture",
        "The diagram below is generated from the full model instance using the `ai_ecosystem.yaml` file content and mermaid to render the diagram.",
        "```mermaid",
        full_mermaid,
        "```",
        "",
        "## 1. Named Cybernetic Feedback Loops",
        "",
        "The model formalizes feedback loops with explicit state variables and mathematical polarity signs:",
        "",
        "| Loop ID | Type | Name | Dynamic Description | Edge Pathway |",
        "| :--- | :---: | :--- | :--- | :--- |",
    ]

    for lp in model.get("loops", []):
        ltype = "**Reinforcing (R)**" if lp.get("loop_type") == "reinforcing" else "*Balancing (B)*"
        edges_str = " →<br/>".join([f"`{e}`" for e in lp.get("loop_edges", [])])
        md.append(f"| `{lp['id']}` | {ltype} | **{lp.get('label', '')}** | {lp.get('description', '')} | {edges_str} |")

    md.extend([
        "",
        "## 2. Viewpoint-Relative VSM Control Frames",
        "",
        "In Beer's Viable System Model (VSM), Systems 1–5 are not intrinsic node tags; they are roles relative to a chosen system-in-focus at a given recursion level:",
        "",
    ])

    for fr in model.get("frames", []):
        offset = fr.get("recursion_offset", 0)
        rec_label = f"Recursion Level {offset:+} ({'Enterprise' if offset == 0 else 'Jurisdiction Meta-System'})"
        md.append(f"### {fr.get('label', fr['id'])} — `{rec_label}`\n")
        md.append(f"> {fr.get('description', '')}\n")
        md.append("| VSM Role | Node | Architectural Rationale |")
        md.append("| :--- | :--- | :--- |")
        for r in fr.get("roles", []):
            md.append(f"| `{r['role']}` | `{r['node']}` | {r.get('rationale', '')} |")
        md.append("")

    md.extend([
        "## 3. Canonical Element Dictionary",
        "",
        "| Element | Cluster | Kind | Wardley Stage | Ashby Variety | Jurisdictions |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    clusters_map = {c["id"]: c["label"] for c in model.get("clusters", [])}
    for n in model["nodes"]:
        cluster_name = clusters_map.get(n.get("cluster", ""), n.get("cluster", ""))
        sub = f"<br/><small>{n['sublabel']}</small>" if n.get("sublabel") else ""
        cardinality_str = format_cardinality(n)
        jurisdictions_str = ", ".join(n.get("jurisdictions", ["global"]))
        evolution = f"`{n.get('evolution_stage')}`" if n.get("evolution_stage") else "—"
        
        md.append(f"| **{n['label']}**{sub}<br/>`{n['id']}` | {cluster_name} | `{n.get('kind', '')}` | {evolution} | {cardinality_str} | `{jurisdictions_str}` |")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] Master documentation generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()