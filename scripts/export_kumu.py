#!/usr/bin/env python3
"""
Kumu Dynamic Blueprint JSON Exporter for AI Ecosystem Model (v3.1).
Outputs: static/exports/ai_ecosystem_kumu.json
Formats:
  - Elements: Node Kind, VSM Roles (Enterprise & Societal), Ashby Variety, Evolution Stage, Jurisdictions, EU AI Act & NIST tags
  - Connections: Semantic Relation Kind, Protocol Plane, Polarity, Affects, Normative Status, Delays, Power Asymmetry, Switching Costs
"""

import sys
import json
import yaml
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RELATION_DOMAINS = {
    "commercial_flow": ["economic"],
    "resource_supply": ["economic", "technical"],
    "statutory_mandate": ["governance"],
    "governance_control": ["governance"],
    "liability_exposure": ["governance", "economic"],
    "competitive_pressure": ["economic"],
    "physical_constraint": ["technical", "economic"],
    "impact": ["governance", "economic"],
    "adversarial_attack": ["technical"],
    "contractual_term": ["economic", "governance"],
    "protocol_call": ["technical"],
    "data_flow": ["technical"],
    "algedonic_signal": ["governance", "technical"],
}

def to_title_header(snake_str):
    acronyms = {
        "eu": "EU", "ai": "AI", "id": "ID", "mcp": "MCP",
        "iam": "IAM", "api": "API", "tos": "ToS", "vsm": "VSM",
        "nist": "NIST", "coala": "CoALA", "rag": "RAG", "gpai": "GPAI"
    }
    words = snake_str.split("_")
    return " ".join(acronyms.get(w.lower(), w.capitalize()) for w in words)

def main():
    model_file = PROJECT_ROOT / "model" / "ai_ecosystem.yaml"
    if not model_file.exists():
        sys.exit(f"[ERROR] Model file not found at: {model_file}")

    with open(model_file, "r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    export_path = PROJECT_ROOT / "static" / "exports"
    export_path.mkdir(parents=True, exist_ok=True)
    target_file = export_path / "ai_ecosystem_kumu.json"

    clusters_map = {c["id"]: c.get("label", c["id"]) for c in model.get("clusters", [])}

    # Map VSM frame roles: (frame_id, node_id) -> role
    vsm_role_map = {}
    for frame in model.get("frames", []):
        fid = frame.get("id")
        for r in frame.get("roles", []):
            vsm_role_map[(fid, r.get("node"))] = r.get("role")

    blueprint = {
        "elements": [],
        "connections": []
    }

    # Build Elements
    for n in model.get("nodes", []):
        domains = n.get("domains", [])
        primary_domain = domains[0].capitalize() if domains else "Entity"
        cid = n.get("cluster", "")
        cluster_name = clusters_map.get(cid, cid)
        
        c_min = n.get("cardinality_log10_min")
        c_max = n.get("cardinality_log10_max")
        c_unit = n.get("cardinality_unit", "")
        variety_str = f"10^{c_min:g}–10^{c_max:g} {c_unit}" if c_min is not None and c_max is not None else ""

        element = {
            "id": n["id"],
            "label": n.get("label", n["id"]),
            "type": primary_domain,
            "description": n.get("sublabel", ""),
            "tags": domains,
            "Kind": to_title_header(n.get("kind", "organisation")),
            "VSM Enterprise": vsm_role_map.get(("F_ENTERPRISE", n["id"]), "Environment / Resource"),
            "VSM Societal": vsm_role_map.get(("F_JURISDICTION", n["id"]), "Environment / Resource"),
            "Jurisdictions": ", ".join(n.get("jurisdictions", ["global"])),
            "Ashby Variety": variety_str,
            "EU AI Act Roles": ", ".join(n.get("eu_ai_act_roles", [])) or "None",
            "NIST Functions": ", ".join(n.get("nist_functions", [])) or "None",
            "Cluster": cluster_name,
            "Cluster ID": cid,
            "Evolution Stage": n.get("evolution_stage") or "Not Applicable"
        }

        # Promote dynamic properties (e.g. compute_profile, capex_cycle, etc.)
        for prop_key, prop_val in n.get("properties", {}).items():
            element[to_title_header(prop_key)] = prop_val

        blueprint["elements"].append(element)

    # Build Connections
    for i, e in enumerate(model.get("edges", [])):
        rkind = e.get("relation_kind", "data_flow")
        pplane = e.get("protocol_plane", "NONE")
        polarity = e.get("polarity", "neutral")
        affects = e.get("affects", "")
        normative = e.get("normative_status", "")
        delay = e.get("delay", "")
        edge_domains = RELATION_DOMAINS.get(rkind, [])

        connection = {
            "id": e.get("id", f"conn_{i}"),
            "from": e["from"],
            "to": e["to"],
            "label": e.get("label", ""),
            "type": rkind,
            "direction": "directed",
            "tags": edge_domains,
            "Protocol Plane": pplane,
            "Polarity": polarity,
            "Affects": affects or "None",
            "Normative Status": normative or "None",
            "Delay": delay or "Immediate",
            "description": f"Kind: {rkind} | Polarity: {polarity}" + (f" | Affects: {affects}" if affects else "")
        }

        if "power_asymmetry" in e:
            connection["Power Asymmetry"] = e["power_asymmetry"]
        if "switching_cost" in e:
            connection["Switching Cost"] = e["switching_cost"]

        blueprint["connections"].append(connection)

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, indent=2, ensure_ascii=False)

    print(f"[OK] Kumu Blueprint JSON created: {target_file.name}")
    print(f"     Elements: {len(blueprint['elements'])}, Connections: {len(blueprint['connections'])}")

if __name__ == "__main__":
    main()