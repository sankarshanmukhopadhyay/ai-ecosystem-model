#!/usr/bin/env python3
"""Run the model's standing inquiries against ai_ecosystem.yaml.

Usage:
  python analyze_ecosystem.py [model.yaml] [inquiry ...] [--remove N_ID,N_ID] [--json]

Inquiries (each answers the question of the matching view):
  chokepoints  Where does power concentrate, and who is locked in?          (V_VALUE_CHAIN)
  liability    When an agent harms someone, who is liable and where does
               recourse break?                                              (V_LIABILITY)
  viability    Are the VSM channels present in each frame?                  (V_*_VSM)
  loops        Which loops exist, how slow are they, which edges are shared? (V_FEEDBACK)
  assurance    Can adverse evidence or a change in authority reach the
               auditor independently, and who can rely on the result?       (V_ASSURANCE)
  all          Everything (default)

--remove deletes nodes first, enabling counterfactual stress testing:
  viability --remove N_SAFETY_INSTITUTE  "What breaks if the safety institutes disappear?"
  liability --remove N_COURTS            "What happens if judicial recourse is unavailable?"

THREE-OUTCOME TYPOLOGY FOR FINDINGS:
  - Type 1: OPERATIONAL [Type 1]         Mechanism exists in model and reality; explains 'how it works'.
  - Type 2: MODEL GAP [Type 2]           Reality has a working practice omitted from the YAML; model needs update.
  - Type 3: REAL-WORLD GAP [Type 3]      Empirical vulnerability, broken recourse, or severed kill-chain in the
                                         wild. DO NOT patch the model with synthetic edges; document the gap!
"""
import sys
import json
from collections import Counter, defaultdict
import yaml

HIGH_SWITCH = {"high", "prohibitive"}
MARKET = {"commercial_flow", "resource_supply", "competitive_pressure", "contractual_term", "protocol_call"}
ROLES = ["s1_operations", "s2_coordination", "s3_control", "s3_star_audit", "s4_intelligence", "s5_policy"]
EVIDENCE_KINDS = {"data_flow", "governance_control", "statutory_mandate", "algedonic_signal"}

def header(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")

def find_path(src, dst, edges, allowed_mid=None):
    """Shortest path over evidence-carrying edges; intermediates must satisfy allowed_mid."""
    queue, seen = [[src]], {src}
    while queue:
        p = queue.pop(0)
        if p[-1] == dst:
            return p
        for e in edges:
            if e["from"] != p[-1] or e["relation_kind"] not in EVIDENCE_KINDS or e["to"] in seen:
                continue
            if e["to"] != dst and allowed_mid is not None and not allowed_mid(e["to"]):
                continue
            seen.add(e["to"])
            queue.append(p + [e["to"]])
    return None


# ------------------------------------------------------------------ chokepoints
def run_chokepoints(nodes, edges):
    holds = defaultdict(list)
    depends = defaultdict(list)
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

    spof = sorted({dom for dom, lst in holds.items() for _, e in lst
                   if nodes[dom]["cardinality_log10_max"] <= 1.5 and e["switching_cost"] == "prohibitive"})
    phys = [e for e in edges if e["relation_kind"] == "physical_constraint"]

    highlight_nodes = set(holds.keys()) | {dep for lst in holds.values() for dep, _ in lst} | set(spof)
    highlight_edges = {e["id"] for lst in holds.values() for _, e in lst} | {e["id"] for e in phys}

    power_holders = []
    for dom, lst in sorted(holds.items(), key=lambda kv: -len({d for d, _ in kv[1]})):
        power_holders.append({
            "dominant_node": dom,
            "cardinality_max": nodes[dom]["cardinality_log10_max"],
            "dependents": [{"node": dep, "edge_id": e["id"], "relation_kind": e["relation_kind"], "switching_cost": e["switching_cost"]}
                           for dep, e in lst]
        })

    most_exposed = []
    for dep, lst in sorted(depends.items(), key=lambda kv: -len({d for d, _ in kv[1]}))[:5]:
        most_exposed.append({
            "dependent_node": dep,
            "dominant_nodes": sorted({d for d, _ in lst})
        })

    return {
        "power_holders": power_holders,
        "most_exposed": most_exposed,
        "single_points_of_failure": spof,
        "physical_ceilings": [{"edge_id": e["id"], "from": e["from"], "to": e["to"], "affects": e.get("affects")} for e in phys],
        "highlight_nodes": sorted(highlight_nodes),
        "highlight_edges": sorted(highlight_edges)
    }

def print_chokepoints(nodes, data):
    name = lambda i: nodes[i]["label"]
    header("CHOKEPOINTS: Power Concentration, Lock-in & Physical Ceilings (V_VALUE_CHAIN)")
    if not data["power_holders"]:
        print("  None detected with high/prohibitive switching cost")
        return

    print("\nPower Holders [Type 1 Market Concentration] (Dependents face high/prohibitive switching cost):")
    for row in data["power_holders"]:
        dom = row["dominant_node"]
        deps = {d["node"] for d in row["dependents"]}
        print(f"  {name(dom):44} dependents={len(deps):<2} population<=10^{row['cardinality_max']:g}")
        for dep_info in row["dependents"]:
            print(f"      -> {name(dep_info['node']):40} [{dep_info['relation_kind']}, {dep_info['switching_cost']}]")

    print("\nMost Exposed Nodes [Captive Dependency]:")
    for row in data["most_exposed"]:
        dep = row["dependent_node"]
        doms = row["dominant_nodes"]
        print(f"  {name(dep):44} dominant counterparties={len(doms)}: " + ", ".join(name(d) for d in doms))

    print("\nSingle Points of Failure [Type 3 Structural Chokepoints] (Population <= 10^1.5 & Prohibitive Switching):")
    for dom in data["single_points_of_failure"]:
        print(f"  ⚠️  {name(dom)} [Single point of physical failure for the global stack]")
    if not data["single_points_of_failure"]:
        print("  None identified")

    if data["physical_ceilings"]:
        print("\nPhysical Ceilings [Type 3 Hard Environmental Constraints]:")
        for phys in data["physical_ceilings"]:
            print(f"  🛑 {name(phys['from'])} -> {name(phys['to'])}: affects '{phys['affects']}'")


# ------------------------------------------------------------------ liability
def run_liability(nodes, edges):
    affected = {n for n, d in nodes.items() if "affected_subject" in d.get("eu_ai_act_roles", [])}
    impacts = [e for e in edges if e["relation_kind"] == "impact" and e["to"] in affected]
    liable = {e["from"] for e in edges if e["relation_kind"] == "liability_exposure" and e["to"] in affected}
    courts = {e["from"] for e in edges if e["relation_kind"] == "statutory_mandate"
              and nodes[e["from"]]["kind"] == "statutory_authority" and e["to"] in liable}
    claims = {e["to"] for e in edges if e["relation_kind"] == "liability_exposure" and e["from"] in affected}

    pay = defaultdict(set)
    for e in edges:
        if e["relation_kind"] == "commercial_flow":
            pay[e["from"]].add(e["to"])

    contract = defaultdict(list)
    for e in edges:
        if e["relation_kind"] == "contractual_term":
            contract[e["to"]].append(e)

    recourse_chains = []
    highlight_edges = {e["id"] for e in impacts}
    for e in edges:
        if (e["relation_kind"] == "liability_exposure" and e["to"] in affected) or \
           (e["relation_kind"] == "liability_exposure" and e["from"] in affected) or \
           (e["relation_kind"] == "statutory_mandate" and e["from"] in courts and e["to"] in liable):
            highlight_edges.add(e["id"])

    for l in liable:
        suppliers = {}
        for s1 in pay[l]:
            suppliers[s1] = 1
            for s2 in pay[s1]:
                suppliers.setdefault(s2, 2)
        sup_rows = []
        for sup, hops in sorted(suppliers.items(), key=lambda kv: kv[1]):
            if nodes[sup]["cluster"] not in ("cluster_supply", "cluster_product"):
                continue
            direct = [e for e in contract[l] if e["from"] == sup]
            if direct:
                for e in direct:
                    state = "DISCLAIMED [Type 3 Liability Gap]" if e["polarity"] == "negative" else "TERMS PRESENT [Type 1]"
                    sup_rows.append({"supplier": sup, "hops": hops, "state": state, "edge_id": e["id"], "label": e["label"]})
                    highlight_edges.add(e["id"])
            else:
                sup_rows.append({"supplier": sup, "hops": hops, "state": "NO RECOURSE EDGE [Type 3 Unallocated Exposure]", "edge_id": None, "label": ""})
        recourse_chains.append({"liable_node": l, "upstream_recourse": sup_rows})

    highlight_nodes = affected | liable | courts | {r["supplier"] for c in recourse_chains for r in c["upstream_recourse"]}
    return {
        "affected_nodes": sorted(affected),
        "impact_edges": [{"edge_id": e["id"], "from": e["from"], "to": e["to"]} for e in impacts],
        "liable_nodes": sorted(liable),
        "courts": sorted(courts),
        "claims_adjudicated": bool(claims & courts),
        "recourse_chains": recourse_chains,
        "highlight_nodes": sorted(highlight_nodes),
        "highlight_edges": sorted(highlight_edges)
    }

def print_liability(nodes, data):
    name = lambda i: nodes[i]["label"]
    header("LIABILITY: Harm, Redress and Upstream Recourse Chains (V_LIABILITY)")
    print("\nHarm Sources (Direct blast-radius impact edges):")
    for imp in data["impact_edges"]:
        print(f"  💥 {name(imp['from'])} -> {name(imp['to'])}")

    print("\nParties Liable to Affected Individuals (Respondeat Superior):",
          ", ".join(name(x) for x in data["liable_nodes"]) or "None identified")

    if data["claims_adjudicated"]:
        print("Adjudication Path (Claim -> Court -> Redress): OPERATIONAL [Type 1] (Statutory claims reach an adjudicator with mandate over the liable party)")
    else:
        print("Adjudication Path (Claim -> Court -> Redress): RECOURSE VOID [Type 3 Real-World Gap] (Claim cannot reach an adjudicator with mandate over the liable party)")

    print("\nUpstream Recourse of Liable Parties (Suppliers paid by the deployer, up to 2 hops):")
    for row in data["recourse_chains"]:
        l = row["liable_node"]
        for sup in row["upstream_recourse"]:
            edge_lbl = f" ({sup['label']})" if sup['label'] else ""
            prefix = "  🛑" if "Type 3" in sup['state'] else "  ✅"
            print(f"{prefix} {name(l)} <- {name(sup['supplier'])} [{sup['hops']} hop]: {sup['state']}{edge_lbl}")


# ------------------------------------------------------------------ viability
def run_viability(nodes, edges, frames):
    frames_analysis = []
    all_hl_nodes, all_hl_edges = set(), set()
    for f in frames:
        roles = defaultdict(list)
        for r in f["roles"]:
            if r["node"] in nodes:
                roles[r["role"]].append(r["node"])
                all_hl_nodes.add(r["node"])
        role_of = {n: r for r, ns in roles.items() for n in ns}

        channels_checked = [
            ("S5 -> S3 (policy/mandate)", {"s5_policy"}, {"s3_control"}, None, False),
            ("S4 -> S5 (intelligence)", {"s4_intelligence"}, {"s5_policy"}, None, False),
            ("S3 -> S1 (control)", {"s3_control"}, {"s1_operations"}, None, False),
            ("S3* -> S1 (audit/probe)", {"s3_star_audit"}, {"s1_operations"}, None, False),
            ("S2 -> S1 (coordination)", {"s2_coordination"}, {"s1_operations"}, None, False),
            ("algedonic -> S5 (alarm bypass)", {"s1_operations"}, {"s5_policy"}, {"algedonic_signal"}, True),
        ]

        channels_res = []
        for label, src_roles, dst_roles, kinds, env_src in channels_checked:
            hits = [e for e in edges
                    if (role_of.get(e["from"]) in src_roles or (env_src and e["from"] not in role_of))
                    and role_of.get(e["to"]) in dst_roles
                    and (kinds is None or e["relation_kind"] in kinds)]
            for h in hits:
                all_hl_edges.add(h["id"])
            channels_res.append({
                "channel": label,
                "status": "OPERATIONAL [Type 1]" if hits else "VIABILITY GAP [Type 3]",
                "edges": [{"edge_id": e["id"], "from": e["from"], "to": e["to"]} for e in hits]
            })

        frames_analysis.append({
            "frame_id": f["id"],
            "label": f["label"],
            "viability_question": f.get("viability_question", ""),
            "roles": {r: roles.get(r, []) for r in ROLES},
            "missing_roles": [r for r in ROLES if not roles.get(r)],
            "channels": channels_res
        })

    return {
        "frames": frames_analysis,
        "highlight_nodes": sorted(all_hl_nodes),
        "highlight_edges": sorted(all_hl_edges)
    }

def print_viability(nodes, data):
    name = lambda i: nodes[i]["label"]
    header("VIABILITY: Cybernetic Roles & Communication Channels (V_*_VSM)")
    for f in data["frames"]:
        print(f"\n{f['label']}")
        print(f"  Viability Inquiry: {f['viability_question'] or '(none)'}")
        for r in ROLES:
            assigned = f["roles"].get(r, [])
            members = ", ".join(name(n) for n in assigned) if assigned else "UNASSIGNED [Type 3 Viability Gap]"
            print(f"  {r:16} {members}")
        print("  Cybernetic Channels:")
        for ch in f["channels"]:
            is_ok = "OPERATIONAL" in ch["status"]
            mark = "ok [Type 1]          " if is_ok else "VIABILITY GAP [Type 3]"
            via = "; ".join(f"{name(e['from'])} -> {name(e['to'])}" for e in ch["edges"][:2])
            via_str = f" via {via}" if via else " (No communication edge exists)"
            print(f"  channel {mark} {ch['channel']:32}{via_str}")


# ------------------------------------------------------------------ loops
def run_loops(nodes, edges, loops_def):
    byid = {e["id"]: e for e in edges}
    use = Counter()
    rank = {"immediate": 0, "months": 1, "years": 2}
    loop_results = []

    for lp in loops_def:
        es = [byid[x] for x in lp["loop_edges"] if x in byid]
        if len(es) != len(lp["loop_edges"]):
            loop_results.append({
                "id": lp["id"], "label": lp["label"], "broken": True,
                "loop_type": lp["loop_type"], "edges": [], "slowest_delay": None, "nodes": []
            })
            continue
        use.update(lp["loop_edges"])
        slowest = max((e.get("delay", "immediate") for e in es), key=rank.get)
        n_years = sum(e.get("delay") == "years" for e in es)
        node_seq = [e["from"] for e in es] + [es[-1]["to"]]

        loop_results.append({
            "id": lp["id"],
            "label": lp["label"],
            "broken": False,
            "loop_type": lp["loop_type"],
            "key_variable": lp.get("key_variable", ""),
            "edges": [e["id"] for e in es],
            "nodes": node_seq,
            "slowest_delay": slowest,
            "delay_years_count": n_years
        })

    shared = [{"edge_id": i, "from": byid[i]["from"], "to": byid[i]["to"], "label": byid[i]["label"], "count": c}
              for i, c in use.items() if c >= 2]
    shared.sort(key=lambda x: -x["count"])

    highlight_nodes = {n for lp in loop_results for n in lp["nodes"]}
    highlight_edges = {e for lp in loop_results for e in lp["edges"]}

    return {
        "loops": loop_results,
        "leverage_points": shared,
        "highlight_nodes": sorted(highlight_nodes),
        "highlight_edges": sorted(highlight_edges)
    }

def print_loops(nodes, data):
    name = lambda i: nodes[i]["label"]
    header("LOOPS: Feedback Topology, Delays and Shared Actuators (V_FEEDBACK)")
    for lp in data["loops"]:
        if lp.get("broken"):
            print(f"\n{lp['label']}: SEVERED by counterfactual node removal [Type 3]")
            continue
        ny = f" ({lp['delay_years_count']} edge(s) take years to propagate)" if lp['delay_years_count'] else ""
        print(f"\n{lp['label']} [{lp['loop_type']}] Key Variable: '{lp['key_variable'] or '?'}'")
        print(f"  {len(lp['edges'])} edges | Bottleneck latency: {lp['slowest_delay']}{ny}")
        print("  Cycle: " + " -> ".join(name(n) for n in lp["nodes"]))

    if data["leverage_points"]:
        print("\nShared Leverage Points [Single Actuators Shared by 2+ Balancing Loops]:")
        for lp in data["leverage_points"]:
            print(f"  ⚡ {lp['count']} loops actuate via: {name(lp['from'])} -> {name(lp['to'])} ({lp['label']})")


# ------------------------------------------------------------------ assurance
def run_assurance(nodes, edges, frames):
    AUDITOR = "N_AUDITOR"
    if AUDITOR not in nodes:
        return {"auditor_present": False, "highlight_nodes": [], "highlight_edges": []}

    frame = next((f for f in frames if f["id"] == "F_ENTERPRISE"), None)
    ent_controlled = {r["node"] for r in frame["roles"]} if frame else set()
    ent_controlled |= {"N_KNOWLEDGE_STORE"} & set(nodes)

    sup = [e for e in edges if e["to"] == AUDITOR and e["relation_kind"] == "statutory_mandate"]
    rel = [e for e in edges if e["from"] == AUDITOR]
    third = [e for e in rel if e["to"] != "N_ENTERPRISE"]

    triggers = [("runtime evaluation (N_OBSERVE)", "N_OBSERVE"),
                ("affected-party complaint (N_AFFECTED_PARTY)", "N_AFFECTED_PARTY"),
                ("civil-society alarm (N_CIVIL_SOCIETY)", "N_CIVIL_SOCIETY"),
                ("regulator action (N_REGULATOR)", "N_REGULATOR")]
    trigger_routes = []
    hl_nodes = {AUDITOR, "N_IDP", "N_TOOL_GATEWAY", "N_AGENT"}
    hl_edges = set()

    for e in sup + rel:
        hl_edges.add(e["id"])
        hl_nodes.add(e["from"])
        hl_nodes.add(e["to"])

    for label, src in triggers:
        if src not in nodes:
            trigger_routes.append({"label": label, "source": src, "available": False, "verdict": "Source node removed in counterfactual"})
            continue
        anyp = find_path(src, AUDITOR, edges)
        indep = None
        if src in ent_controlled:
            verdict = "N/A (Telemetry is enterprise-operated, not independent)"
        else:
            indep = find_path(src, AUDITOR, edges, allowed_mid=lambda n: n not in ent_controlled)
            if indep:
                verdict = "INDEPENDENT [Type 1]: " + " > ".join(nodes[n]["label"] for n in indep)
            else:
                verdict = "INSULATED [Type 3 Gap]: Route passes through enterprise-controlled systems"

        if anyp:
            for a, b in zip(anyp, anyp[1:]):
                matching = [e["id"] for e in edges if e["from"] == a and e["to"] == b and e["relation_kind"] in EVIDENCE_KINDS]
                if matching:
                    hl_edges.add(matching[0])
            hl_nodes.update(anyp)

        trigger_routes.append({
            "label": label,
            "source": src,
            "available": True,
            "any_route": bool(anyp),
            "independent_path": indep,
            "verdict": verdict
        })

    idp_in = [e for e in edges if e["to"] == "N_IDP" and e["relation_kind"] == "governance_control"]
    idp_gw = [e for e in edges if e["from"] == "N_IDP" and e["to"] == "N_TOOL_GATEWAY"]
    idp_ag = [e for e in edges if e["from"] == "N_IDP" and e["to"] == "N_AGENT"]
    for e in idp_in + idp_gw + idp_ag:
        hl_edges.add(e["id"])
        hl_nodes.add(e["from"])
        hl_nodes.add(e["to"])

    return {
        "auditor_present": True,
        "supervision_edges": [{"edge_id": e["id"], "from": e["from"], "normative_status": e.get("normative_status")} for e in sup],
        "reliance_edges": [{"edge_id": e["id"], "to": e["to"], "is_third_party": e in third} for e in rel],
        "trigger_routes": trigger_routes,
        "authority_chain": {
            "principal_to_idp": bool(idp_in),
            "idp_to_agent": bool(idp_ag),
            "idp_to_gateway": bool(idp_gw)
        },
        "highlight_nodes": sorted(hl_nodes & set(nodes)),
        "highlight_edges": sorted(hl_edges)
    }

def print_assurance(nodes, data):
    name = lambda i: nodes[i]["label"]
    header("ASSURANCE: Continuing Assurance, Independent Alarms & Revocation (V_ASSURANCE)")
    if not data["auditor_present"]:
        print("  ⚠️  N_AUDITOR removed: No independent conformity baseline exists in this frame")
        return

    print("\nSupervisory Oversight over Conformity Body (Recognition, Supervision, Suspension):")
    for s in data["supervision_edges"]:
        print(f"  ✅ {name(s['from'])} [{s['normative_status']}] -> Holds statutory reassessment mandate over auditor")
    if not data["supervision_edges"]:
        print("  🛑 GOVERNANCE GAP [Type 3]: No external authority holds a mandate to suspend or reassess the auditor")

    print("\nDownstream Reliance on Conformity Determination:")
    for r in data["reliance_edges"]:
        tag = "Third-Party Underwriting Gate [Type 1]" if r["is_third_party"] else "Assessed Enterprise Internal Use"
        print(f"  ✅ {name(r['to'])} ({tag})")
    if not any(r["is_third_party"] for r in data["reliance_edges"]):
        print("  🛑 ECONOMIC DISCONNECT [Type 3]: No third-party relies on determination (certification is decorative)")

    print("\nAdverse Evidence Routes to Auditor (Post-Market Surveillance):")
    print(f"  {'Trigger Source':42} {'Route':8} {'Independence Verdict'}")
    for tr in data["trigger_routes"]:
        if not tr["available"]:
            print(f"  {tr['label']:42} (Removed in counterfactual)")
            continue
        route_str = "Yes" if tr["any_route"] else "None"
        print(f"  {tr['label']:42} {route_str:<8} {tr['verdict']}")

    ac = data["authority_chain"]
    print("\nDelegated Authority Kill-Chain (Principal -> IdP -> Tool Gateway):")
    p_to_idp = "OPERATIONAL [Type 1]" if ac['principal_to_idp'] else "GOVERNANCE GAP [Type 3] (Principal lacks IAM governance line)"
    idp_to_ag = "OPERATIONAL [Type 1]" if ac['idp_to_agent'] else "AUTHENTICATION GAP [Type 3] (Agent operates without managed IAM tokens)"
    idp_to_gw = "OPERATIONAL [Type 1]" if ac['idp_to_gateway'] else "REAL-WORLD GAP [Type 3] (Gateway does not introspect tokens; agent retains reach after revocation)"

    print(f"  1. Principal grants/revokes via IdP       : {p_to_idp}")
    print(f"  2. IdP issues short-lived A2E credentials : {idp_to_ag}")
    print(f"  3. Gateway validates tokens at call time  : {idp_to_gw}")


# ------------------------------------------------------------------ main execution
def run_all_inquiries(nodes, edges, frames, loops):
    return {
        "chokepoints": run_chokepoints(nodes, edges),
        "liability": run_liability(nodes, edges),
        "viability": run_viability(nodes, edges, frames),
        "loops": run_loops(nodes, edges, loops),
        "assurance": run_assurance(nodes, edges, frames)
    }

def main():
    args = [a for a in sys.argv[1:]]
    json_output = "--json" in args
    if json_output:
        args.remove("--json")

    remove = set()
    if "--remove" in args:
        i = args.index("--remove")
        remove = set(args[i + 1].split(","))
        del args[i:i + 2]

    path = next((a for a in args if a.endswith(".yaml")), "model/ai_ecosystem.yaml")
    wanted = [a for a in args if not a.endswith(".yaml")] or ["all"]

    try:
        M = yaml.safe_load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        M = yaml.safe_load(open("ai_ecosystem.yaml", encoding="utf-8"))

    for r in remove:
        if r not in {n["id"] for n in M["nodes"]}:
            sys.exit(f"unknown node to remove: {r}")

    nodes = {n["id"]: n for n in M["nodes"] if n["id"] not in remove}
    edges = [e for e in M["edges"] if e["from"] in nodes and e["to"] in nodes]
    frames = M.get("frames", [])
    loops = M.get("loops", [])

    results = {}
    if "all" in wanted or "chokepoints" in wanted:
        results["chokepoints"] = run_chokepoints(nodes, edges)
    if "all" in wanted or "liability" in wanted:
        results["liability"] = run_liability(nodes, edges)
    if "all" in wanted or "viability" in wanted:
        results["viability"] = run_viability(nodes, edges, frames)
    if "all" in wanted or "loops" in wanted:
        results["loops"] = run_loops(nodes, edges, loops)
    if "all" in wanted or "assurance" in wanted:
        results["assurance"] = run_assurance(nodes, edges, frames)

    if json_output:
        print(json.dumps(results, indent=2, default=str))
        return

    if remove:
        print(f"Counterfactual simulation: Removed nodes: {', '.join(sorted(remove))} ({len(M['edges']) - len(edges)} edges dropped)")

    printers = {
        "chokepoints": lambda: print_chokepoints(nodes, results["chokepoints"]),
        "liability": lambda: print_liability(nodes, results["liability"]),
        "viability": lambda: print_viability(nodes, results["viability"]),
        "loops": lambda: print_loops(nodes, results["loops"]),
        "assurance": lambda: print_assurance(nodes, results["assurance"])
    }

    for key in (printers if "all" in wanted else wanted):
        if key not in printers:
            sys.exit(f"unknown inquiry '{key}'. Choose from {list(printers)} or 'all'.")
        printers[key]()

if __name__ == "__main__":
    main()