#!/usr/bin/env python3
"""
Compiles model/ai_ecosystem.yaml and standing inquiry results into static/data/ecosystem_bundle.json.
This single JSON bundle feeds the interactive Cytoscape viewer and web projections.
"""

import sys
import json
import yaml
from datetime import date, datetime
from pathlib import Path

# Add current scripts directory to import analyze_ecosystem
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import analyze_ecosystem

MODEL_FILE = PROJECT_ROOT / "model" / "ai_ecosystem.yaml"
OUTPUT_DIR = PROJECT_ROOT / "static" / "data"
OUTPUT_FILE = OUTPUT_DIR / "ecosystem_bundle.json"

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

def json_serial(obj):
    """JSON serializer for objects not serializable by default (e.g., date, datetime)."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return str(obj)

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
        sys.exit(f"[ERROR] Model file not found: {MODEL_FILE}")

    with open(MODEL_FILE, "r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    nodes_dict = {n["id"]: n for n in model.get("nodes", [])}
    edges_list = model.get("edges", [])
    frames_list = model.get("frames", [])
    loops_list = model.get("loops", [])
    clusters_list = model.get("clusters", [])
    views_list = model.get("views", [])

    # 1. Precalculate VSM assignments per node
    vsm_map = {}
    for frame in frames_list:
        fid = frame["id"]
        for r in frame.get("roles", []):
            vsm_map.setdefault(r["node"], {})[fid] = r["role"]

    # 2. Enrich nodes
    enriched_nodes = []
    for n in model.get("nodes", []):
        nid = n["id"]
        enriched_node = dict(n)
        enriched_node["ashby_variety"] = format_cardinality(n)
        enriched_node["vsm_roles"] = vsm_map.get(nid, {})
        enriched_nodes.append(enriched_node)

    # 3. Enrich edges with derived domains and preserve jurisdictions
    enriched_edges = []
    for e in edges_list:
        ee = dict(e)
        ee["domains"] = RELATION_DOMAINS.get(e.get("relation_kind"), ["technical"])
        ee["jurisdictions"] = e.get("jurisdictions", ["global"])
        enriched_edges.append(ee)

    # 4. Run standing inquiries to generate active overlays
    print("[BUNDLE] Computing analytical overlays from standing inquiries...")
    inquiries_data = analyze_ecosystem.run_all_inquiries(nodes_dict, edges_list, frames_list, loops_list)

    # 5. Build bundle payload
    bundle = {
        "metadata": model.get("metadata", {}),
        "clusters": clusters_list,
        "nodes": enriched_nodes,
        "edges": enriched_edges,
        "loops": loops_list,
        "frames": frames_list,
        "views": views_list,
        "inquiries": inquiries_data,
        "relation_domains": RELATION_DOMAINS
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(bundle, out, indent=2, ensure_ascii=False, default=json_serial)

    print(f"[OK] Viewer bundle exported successfully: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")
    print(f"     Nodes: {len(enriched_nodes)} | Edges: {len(enriched_edges)} | Views: {len(views_list)} | Inquiries: {len(inquiries_data)}")

if __name__ == "__main__":
    main()