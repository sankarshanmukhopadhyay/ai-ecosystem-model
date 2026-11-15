#!/usr/bin/env python3
"""Validate ai_ecosystem.yaml against ai_ecosystem_schema.yaml.

Covers what plain LinkML validation does not: relational checks (min <= max, loop contiguity,
frame completeness, algedonic wiring, orphans) plus the schema's conditional rules, which are
re-implemented here so the checks run without the linkml package.
Usage: python validate_ecosystem.py [model.yaml] [schema.yaml] [--refs doc.md ...]

--refs also checks inquiry pages or other documents against the model:
  - every node/edge/loop/frame/view id (N_*, E_*, L_*, F_*, V_*) must exist (errors; old v2 ids get a hint)
  - every "N_A -> N_B" relationship claim must be backed by an edge (warnings: label it a hypothesis
    or add the edge with defensible semantics)
"""
import re
import sys
from collections import Counter

import yaml

_args = sys.argv[1:]
ref_docs = []
if "--refs" in _args:
    _i = _args.index("--refs")
    ref_docs = _args[_i + 1:]
    _args = _args[:_i]
model_path = _args[0] if len(_args) > 0 else "ai_ecosystem.yaml"
schema_path = _args[1] if len(_args) > 1 else "ai_ecosystem_schema.yaml"
M = yaml.safe_load(open(model_path, encoding="utf-8"))
S = yaml.safe_load(open(schema_path, encoding="utf-8"))
enums = {k: set(v["permissible_values"]) for k, v in S["enums"].items()}

errors, warnings = [], []
err = errors.append
warn = warnings.append


def check_enum(where, value, enum):
    vals = value if isinstance(value, list) else [value]
    for v in vals:
        if v not in enums[enum]:
            err(f"{where}: '{v}' not in {enum}")


clusters = {c["id"] for c in M["clusters"]}
nodes = {n["id"]: n for n in M["nodes"]}
edges = {e["id"]: e for e in M["edges"]}
for label, items in (("node", M["nodes"]), ("edge", M["edges"]), ("cluster", M["clusters"])):
    dup = [k for k, c in Counter(i["id"] for i in items).items() if c > 1]
    if dup:
        err(f"duplicate {label} ids: {dup}")

# ---------------- nodes ----------------
no_evo = {"public_authority", "statutory_authority", "private_oversight_body", "person", "threat_actor"}
node_enum_slots = {
    "kind": "NodeKindEnum", "evolution_stage": "EvolutionStageEnum", "jurisdictions": "JurisdictionEnum",
    "regime_types": "RegimeTypeEnum", "eu_ai_act_roles": "EuAiActRoleEnum",
    "nist_functions": "NistRmfFunctionEnum", "cardinality_unit": "CardinalityUnitEnum",
    "confidence": "ConfidenceEnum", "domains": "DomainEnum",
}
for n in M["nodes"]:
    w = f"node {n['id']}"
    for slot in ("cluster", "domains", "kind", "cardinality_log10_min", "cardinality_log10_max", "cardinality_unit"):
        if slot not in n:
            err(f"{w}: missing required '{slot}'")
    if n.get("cluster") not in clusters:
        err(f"{w}: unknown cluster {n.get('cluster')}")
    for slot, enum in node_enum_slots.items():
        if slot in n:
            check_enum(f"{w}.{slot}", n[slot], enum)
    if n.get("cardinality_log10_min", 0) > n.get("cardinality_log10_max", 0):
        err(f"{w}: cardinality min > max")
    if n.get("kind") in no_evo and "evolution_stage" in n:
        err(f"{w}: evolution_stage not allowed for kind {n['kind']}")

# ---------------- edges ----------------
no_market = {"statutory_mandate", "governance_control", "liability_exposure", "physical_constraint",
             "adversarial_attack", "impact", "data_flow", "algedonic_signal"}
needs_norm = {"statutory_mandate", "governance_control", "contractual_term"}
deg = Counter()
for e in M["edges"]:
    w = f"edge {e['id']}"
    for end in ("from", "to"):
        if e.get(end) not in nodes:
            err(f"{w}: unknown {end} node {e.get(end)}")
    deg[e.get("from")] += 1
    deg[e.get("to")] += 1
    rk = e.get("relation_kind")
    check_enum(f"{w}.relation_kind", rk, "RelationKindEnum")
    check_enum(f"{w}.polarity", e.get("polarity"), "PolarityEnum")
    for slot, enum in (("protocol_plane", "ProtocolPlaneEnum"), ("power_asymmetry", "PowerAsymmetryEnum"),
                       ("switching_cost", "SwitchingCostEnum"), ("normative_status", "NormativeStatusEnum"),
                       ("delay", "DelayEnum")):
        if slot in e:
            check_enum(f"{w}.{slot}", e[slot], enum)
    if (rk == "protocol_call") != ("protocol_plane" in e):
        err(f"{w}: protocol_plane must be present iff relation_kind == protocol_call")
    if rk in no_market and ("power_asymmetry" in e or "switching_cost" in e):
        err(f"{w}: market fields not allowed on {rk}")
    if (rk in needs_norm) != ("normative_status" in e):
        err(f"{w}: normative_status must be present iff relation_kind in {sorted(needs_norm)}")
    pol = e.get("polarity")
    if pol in ("positive", "negative") and not e.get("affects"):
        err(f"{w}: signed polarity requires 'affects'")
    if pol == "neutral" and "affects" in e:
        err(f"{w}: neutral edge must not have 'affects'")
    if "domains" in e:
        err(f"{w}: 'domains' is derived from relation_kind; remove it")

for nid in nodes:
    if deg[nid] == 0:
        warn(f"orphan node {nid}")
    elif deg[nid] == 1:
        warn(f"thinly connected node {nid} (1 edge)")

# ---------------- loops ----------------
for lp in M.get("loops", []):
    w = f"loop {lp['id']}"
    check_enum(f"{w}.loop_type", lp["loop_type"], "LoopTypeEnum")
    if not lp.get("key_variable"):
        warn(f"{w}: no key_variable")
    if not any("delay" in edges[x] for x in lp["loop_edges"] if x in edges):
        warn(f"{w}: no delay recorded on any edge")
    es = []
    for eid in lp["loop_edges"]:
        if eid not in edges:
            err(f"{w}: unknown edge {eid}")
        else:
            es.append(edges[eid])
    if len(es) != len(lp["loop_edges"]):
        continue
    for a, b in zip(es, es[1:]):
        if a["to"] != b["from"]:
            err(f"{w}: not contiguous at {a['id']} -> {b['id']}")
    if es and es[-1]["to"] != es[0]["from"]:
        err(f"{w}: does not close (last edge ends at {es[-1]['to']}, first starts at {es[0]['from']})")
    sign = {"positive": 1, "negative": -1}
    parity = 1
    for e in es:
        parity *= sign.get(e["polarity"], 1)
    implied = "reinforcing" if parity > 0 else "balancing"
    if implied != lp["loop_type"]:
        warn(f"{w}: declared {lp['loop_type']} but polarity parity implies {implied} (advisory)")

# ---------------- VSM frames ----------------
roles_needed = {"s1_operations", "s2_coordination", "s3_control", "s3_star_audit", "s4_intelligence", "s5_policy"}
frames = {f["id"]: f for f in M.get("frames", [])}
role_of = {}
for fid, f in frames.items():
    seen = {}
    for field in ("system_boundary", "viability_question"):
        if not f.get(field):
            warn(f"frame {fid}: missing {field}")
    for r in f["roles"]:
        w = f"frame {fid}"
        if r["node"] not in nodes:
            err(f"{w}: unknown node {r['node']}")
        check_enum(f"{w}.role", r["role"], "VsmRoleEnum")
        seen.setdefault(r["node"], []).append(r["role"])
        role_of[(fid, r["node"])] = r["role"]
    for nid, rs in seen.items():
        if len(set(rs)) > 1:
            err(f"frame {fid}: node {nid} has conflicting roles {rs}")
    missing = roles_needed - {r["role"] for r in f["roles"]}
    if missing:
        warn(f"frame {fid}: viability gap, no node for {sorted(missing)}")

# Algedonic edges should run from S1 (or the environment) to S5 in some frame
for e in M["edges"]:
    if e["relation_kind"] != "algedonic_signal":
        continue
    ok = False
    for fid in frames:
        src = role_of.get((fid, e["from"]))
        dst = role_of.get((fid, e["to"]))
        if dst == "s5_policy" and src in (None, "s1_operations"):
            ok = True
    if not ok:
        warn(f"algedonic edge {e['id']} does not run S1/environment -> S5 in any frame")

# ---------------- views ----------------
loop_ids = {lp["id"] for lp in M.get("loops", [])}
for v in M.get("views", []):
    w = f"view {v['id']}"
    if "question" not in v:
        warn(f"{w}: no question")
    for rk in v.get("relation_kinds", []):
        check_enum(f"{w}.relation_kinds", rk, "RelationKindEnum")
    for nid in v.get("focus_nodes", []):
        if nid not in nodes:
            err(f"{w}: unknown focus node {nid}")
    if "frame" in v and v["frame"] not in frames:
        err(f"{w}: unknown frame {v['frame']}")
    for lid in v.get("loops_shown", []):
        if lid not in loop_ids:
            err(f"{w}: unknown loop {lid}")
    if "direction" in v:
        check_enum(f"{w}.direction", v["direction"], "DirectionEnum")

# ---------------- document references ----------------
MIGRATED = {  # ids removed or split in v3.x
    "N_HARNESS": "split into N_AGENT (runtime) and N_GUARDRAIL (policy kernel)",
    "N_FRONTIER": "split into N_FRONTIER_LAB (organisation) and N_FRONTIER_MODEL (artefact)",
    "N_ABSORBED": "now the competitive_pressure edges E_LAB_ABSORBS_ISV and E_CLOUD_ABSORBS_ISV",
    "N_ISV": "renamed N_ISV_PRODUCT",
}
if ref_docs:
    all_ids = set(nodes) | set(edges) | {lp["id"] for lp in M.get("loops", [])} | set(frames) \
        | {v["id"] for v in M.get("views", [])}
    pairs = {(e["from"], e["to"]) for e in M["edges"]}
    id_re = re.compile(r"\b[NELFV]_[A-Z][A-Z0-9_]*\b")
    claim_re = re.compile(r"\b(N_[A-Z][A-Z0-9_]*)\s*(?:→|->|⟶)\s*(N_[A-Z][A-Z0-9_]*)")
    for doc in ref_docs:
        try:
            lines = open(doc, encoding="utf-8").read().splitlines()
        except OSError as ex:
            err(f"{doc}: cannot read ({ex})")
            continue
        for ln, text in enumerate(lines, 1):
            for ident in sorted(set(id_re.findall(text))):
                if ident not in all_ids:
                    hint = f" ({MIGRATED[ident]})" if ident in MIGRATED else ""
                    err(f"{doc}:{ln}: unknown id {ident}{hint}")
            for a, b in claim_re.findall(text):
                if a in nodes and b in nodes and (a, b) not in pairs:
                    warn(f"{doc}:{ln}: no edge {a} -> {b}; present as a hypothesis or add a defensible edge")

# ---------------- report ----------------
print(f"{len(nodes)} nodes, {len(edges)} edges, {len(M.get('loops', []))} loops, "
      f"{len(frames)} frames, {len(M.get('views', []))} views")
print("Relation kinds:", dict(Counter(e["relation_kind"] for e in M["edges"])))
print(f"\nERRORS ({len(errors)})")
for x in errors:
    print("  -", x)
print(f"\nWARNINGS ({len(warnings)})")
for x in warnings:
    print("  -", x)
sys.exit(1 if errors else 0)
