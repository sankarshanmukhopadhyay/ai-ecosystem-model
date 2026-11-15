#!/usr/bin/env python3
"""Run the model's standing inquiries against ai_ecosystem.yaml.

Usage:
  python analyze_ecosystem.py [model.yaml] [inquiry ...] [--remove N_ID,N_ID]

Inquiries (each answers the question of the matching view):
  chokepoints  Where does power concentrate, and who is locked in?          (V_VALUE_CHAIN)
  liability    When an agent harms someone, who is liable and where does
               recourse break?                                              (V_LIABILITY)
  viability    Are the VSM channels present in each frame?                  (V_*_VSM)
  loops        Which loops exist, how slow are they, which edges are shared? (V_FEEDBACK)
  all          Everything (default)

--remove deletes nodes first, so `viability --remove N_SAFETY_INSTITUTE` answers
"what breaks if the safety institutes disappear?".
"""
import sys
from collections import Counter, defaultdict

import yaml

args = [a for a in sys.argv[1:]]
remove = set()
if "--remove" in args:
    i = args.index("--remove")
    remove = set(args[i + 1].split(","))
    del args[i:i + 2]
path = next((a for a in args if a.endswith(".yaml")), "ai_ecosystem.yaml")
wanted = [a for a in args if not a.endswith(".yaml")] or ["all"]
M = yaml.safe_load(open(path, encoding="utf-8"))

for r in remove:
    if r not in {n["id"] for n in M["nodes"]}:
        sys.exit(f"unknown node to remove: {r}")
nodes = {n["id"]: n for n in M["nodes"] if n["id"] not in remove}
edges = [e for e in M["edges"] if e["from"] in nodes and e["to"] in nodes]
byid = {e["id"]: e for e in edges}
name = lambda i: nodes[i]["label"]
HIGH_SWITCH = {"high", "prohibitive"}
MARKET = {"commercial_flow", "resource_supply", "competitive_pressure", "contractual_term", "protocol_call"}


def header(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


# ------------------------------------------------------------------ chokepoints
def chokepoints():
    header("CHOKEPOINTS: who holds power over whom, with high switching cost")
    holds = defaultdict(list)    # dominant node -> [(dependent, edge)]
    depends = defaultdict(list)  # dependent node -> [(dominant, edge)]
    for e in edges:
        if e["relation_kind"] not in MARKET or e.get("switching_cost") not in HIGH_SWITCH:
            continue
        pa = e.get("power_asymmetry")
        if pa == "source_dominant":
            dom, dep = e["from"], e["to"]
        elif pa == "target_dominant":
            dom, dep = e["to"], e["from"]
        else:
            continue
        holds[dom].append((dep, e))
        depends[dep].append((dom, e))
    if not holds:
        print("  none found")
        return
    print("\nPower holders (dependents with high/prohibitive switching cost):")
    rows = sorted(holds.items(), key=lambda kv: -len({d for d, _ in kv[1]}))
    for dom, lst in rows:
        card = nodes[dom]["cardinality_log10_max"]
        print(f"  {name(dom):44} dependents={len({d for d, _ in lst})}  population<=10^{card:g}")
        for dep, e in lst:
            print(f"      -> {name(dep):40} [{e['relation_kind']}, {e['switching_cost']}]")
    print("\nMost exposed (dependent on the most dominant parties):")
    for dep, lst in sorted(depends.items(), key=lambda kv: -len({d for d, _ in kv[1]}))[:5]:
        print(f"  {name(dep):44} dominant parties={len({d for d, _ in lst})}: "
              + ", ".join(sorted({name(d) for d, _ in lst})))
    print("\nSingle points of failure (dominant, population <= 10^1.5, prohibitive switching):")
    spof = [(dom, e) for dom, lst in holds.items() for _, e in lst
            if nodes[dom]["cardinality_log10_max"] <= 1.5 and e["switching_cost"] == "prohibitive"]
    for dom in sorted({d for d, _ in spof}):
        print(f"  {name(dom)}")
    if not spof:
        print("  none")
    phys = [e for e in edges if e["relation_kind"] == "physical_constraint"]
    if phys:
        print("\nPhysical ceilings:")
        for e in phys:
            print(f"  {name(e['from'])} -> {name(e['to'])}: {e['affects']}")


# ------------------------------------------------------------------ liability
def liability():
    header("LIABILITY: harm, liability, redress and recourse")
    affected = {n for n, d in nodes.items() if "affected_subject" in d.get("eu_ai_act_roles", [])}
    impacts = [e for e in edges if e["relation_kind"] == "impact" and e["to"] in affected]
    print("\nHarm sources (impact edges):")
    for e in impacts:
        print(f"  {name(e['from'])} -> {name(e['to'])}")
    liable = {e["from"] for e in edges if e["relation_kind"] == "liability_exposure" and e["to"] in affected}
    print("\nParties modelled as liable to affected persons:", ", ".join(name(x) for x in liable) or "none")
    courts = {e["from"] for e in edges if e["relation_kind"] == "statutory_mandate"
              and nodes[e["from"]]["kind"] == "statutory_authority" and e["to"] in liable}
    claims = {e["to"] for e in edges if e["relation_kind"] == "liability_exposure" and e["from"] in affected}
    print("Adjudication path (claim -> ruling):",
          "complete" if claims & courts else "BROKEN: no claim edge reaches an adjudicator that rules on the liable party")
    pay = defaultdict(set)  # payer -> payees (commercial_flow)
    for e in edges:
        if e["relation_kind"] == "commercial_flow":
            pay[e["from"]].add(e["to"])
    contract = defaultdict(list)  # recipient of contractual terms -> edges
    for e in edges:
        if e["relation_kind"] == "contractual_term":
            contract[e["to"]].append(e)
    print("\nRecourse upstream of each liable party (suppliers it pays, up to 2 hops):")
    for l in liable:
        suppliers = {}
        for s1 in pay[l]:
            suppliers[s1] = 1
            for s2 in pay[s1]:
                suppliers.setdefault(s2, 2)
        for sup, hops in sorted(suppliers.items(), key=lambda kv: kv[1]):
            if nodes[sup]["cluster"] not in ("cluster_supply", "cluster_product"):
                continue  # insurers and other non-suppliers are not recourse targets
            direct = [e for e in contract[l] if e["from"] == sup]
            if direct:
                for e in direct:
                    state = "DISCLAIMED" if e["polarity"] == "negative" else "term present"
                    print(f"  {name(l)} <- {name(sup)} [{hops} hop]: {state} ({e['label']})")
            else:
                print(f"  {name(l)} <- {name(sup)} [{hops} hop]: NO recourse edge modelled")


# ------------------------------------------------------------------ viability
ROLES = ["s1_operations", "s2_coordination", "s3_control", "s3_star_audit", "s4_intelligence", "s5_policy"]


def viability():
    header("VIABILITY: VSM functions and channels per frame")
    for f in M["frames"]:
        roles = defaultdict(list)
        for r in f["roles"]:
            if r["node"] in nodes:
                roles[r["role"]].append(r["node"])
        role_of = {n: r for r, ns in roles.items() for n in ns}
        print(f"\n{f['label']}")
        print(f"  question: {f.get('viability_question', '(none)')}")
        for r in ROLES:
            members = ", ".join(name(n) for n in roles.get(r, [])) or "MISSING"
            print(f"  {r:16} {members}")

        def chan(label, src_roles, dst_roles, kinds=None, env_src=False):
            hits = [e for e in edges
                    if (role_of.get(e["from"]) in src_roles or (env_src and e["from"] not in role_of))
                    and role_of.get(e["to"]) in dst_roles
                    and (kinds is None or e["relation_kind"] in kinds)]
            mark = "ok     " if hits else "MISSING"
            via = "; ".join(f"{name(e['from'])} -> {name(e['to'])}" for e in hits[:2])
            print(f"  channel {mark} {label:30} {via}")

        print("  Channels:")
        chan("S5 -> S3 (policy/mandate)", {"s5_policy"}, {"s3_control"})
        chan("S4 -> S5 (intelligence)", {"s4_intelligence"}, {"s5_policy"})
        chan("S3 -> S1 (control)", {"s3_control"}, {"s1_operations"})
        chan("S3* -> S1 (audit/probe)", {"s3_star_audit"}, {"s1_operations"})
        chan("S2 -> S1 (coordination)", {"s2_coordination"}, {"s1_operations"})
        chan("algedonic -> S5", {"s1_operations"}, {"s5_policy"}, {"algedonic_signal"}, env_src=True)


# ------------------------------------------------------------------ loops
def loops():
    header("LOOPS: structure, speed and leverage points")
    use = Counter()
    rank = {"immediate": 0, "months": 1, "years": 2}
    for lp in M["loops"]:
        es = [byid[x] for x in lp["loop_edges"] if x in byid]
        if len(es) != len(lp["loop_edges"]):
            print(f"\n{lp['label']}: BROKEN by removed nodes")
            continue
        use.update(lp["loop_edges"])
        slowest = max((e.get("delay", "immediate") for e in es), key=rank.get)
        n_years = sum(e.get("delay") == "years" for e in es)
        print(f"\n{lp['label']} [{lp['loop_type']}] key variable: {lp.get('key_variable', '?')}")
        print(f"  {len(es)} edges, slowest link: {slowest}" + (f" ({n_years} such)" if n_years else ""))
        print("  " + " -> ".join(name(e['from']) for e in es) + f" -> {name(es[-1]['to'])}")
    shared = [(i, c) for i, c in use.items() if c >= 2]
    if shared:
        print("\nLeverage points (edges shared by 2+ loops):")
        for i, c in sorted(shared, key=lambda x: -x[1]):
            e = byid[i]
            print(f"  {c} loops: {name(e['from'])} -> {name(e['to'])} ({e['label']})")


# ------------------------------------------------------------------ main
if remove:
    print(f"Removed nodes: {', '.join(sorted(remove))} ({len(M['edges']) - len(edges)} edges dropped)")
run = {"chokepoints": chokepoints, "liability": liability, "viability": viability, "loops": loops}
for key in (run if "all" in wanted else wanted):
    if key not in run:
        sys.exit(f"unknown inquiry '{key}'. Choose from {list(run)} or 'all'.")
    run[key]()
