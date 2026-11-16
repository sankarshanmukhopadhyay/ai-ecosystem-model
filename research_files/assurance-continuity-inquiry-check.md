# Assurance-continuity inquiry: grounding check

This is a bounded review scenario for the [inquiry protocol](../prompts/inquiry_protocol.md), not a replacement for the published [standards and certification inquiry](../docs/inquiries/inq-standards-certification-efficiency.md). It tests whether the two-stage dialogue-to-artifact process preserves the model's explanatory limits. The canonical model, not this note, owns the graph.

## Scenario

A previously assessed AI deployment changes its operating configuration or delegated authority. Runtime evaluation and an affected-party complaint produce adverse observations. A relying party must decide whether the original assurance determination can still be relied upon, even though the certificate's formal status may not have changed.

Ask in Phase 1:

> How does the current AI Ecosystem Model explain the route from adverse observations to reassessment, changes in assurance status, and third-party reliance? What can it establish from the graph alone, and what does it leave unresolved?

Then request `Draft the inquiry artifact` using the repository's [inquiry protocol](../prompts/inquiry_protocol.md), without manually adding nodes or edges.

## Canonical grounding anchors

Verify these against the **current** `model/ai_ecosystem.yaml` before evaluating a generated response. They are examples of represented relationships, not assertions that the whole assurance process is complete.

| Canonical element | What it establishes | What it does not establish |
| --- | --- | --- |
| `E_REG_TO_AUDITOR` | Recognition, supervision, suspension of conformity bodies, and the possibility of regulator-required reassessment. | That every certificate has been suspended, or that the regulator itself made a particular certificate determination. |
| `E_OBSERVE_TO_AUDITOR` | A behavioural-evaluation evidence flow to the assessor. | Evidence independence: the edge explicitly describes enterprise-operated evaluation. |
| `E_AUDIT_TO_AUDITOR` | An audit-store evidence flow to the assessor. | Completeness or truth of the captured activity. |
| `E_AUDITOR_TO_ENT` | Conformity audits and certification directed toward the assessed enterprise. | A versioned certificate-status lifecycle or unrestricted operating permission. |
| `E_AUDITOR_TO_INSURER` | Certification status and scope can reach an insurer as a reliance input. | The insurer's actual underwriting decision or the legal validity of third-party reliance. |
| `E_AFFECTED_TO_REG_COMPLAINT` | A complaint can reach the regulator. | Its admissibility, evaluation, or automatic effect on a certificate. |

The current model distinguishes `N_AUDITOR` (`private_oversight_body`) from `N_REGULATOR` (`statutory_authority`). Do not reintroduce the older claim that the assessor is typed as a statutory authority.

## Checks to perform

1. **Graph facts:** Every claimed canonical node and directed relationship exists. An intermediate path may be explained, but must not be promoted into an unmodelled direct mandate or guaranteed outcome.
2. **Governance semantics:** Separate recognition or supervision of an assessor, reassessment of an assessed system, certificate status, continuing applicability of underlying evidence, and a relying party's decision. Do not equate these.
3. **Evidence status:** Distinguish enterprise-operated observations from independent assessment. Do not infer independence from a node label, a data-flow edge, or tamper-evident storage.
4. **External claims:** Attribute specific legal powers, certification rules, or causal market effects to external evidence rather than treating them as graph facts.
5. **Gap handling:** If a material question is not answerable, identify whether the missing element is a node, relationship, attribute, condition, empirical fact, or explicit modelling boundary. Do not automatically prescribe an additional node.
6. **Dialogue-to-artifact fidelity:** Compare the exploratory answer with the published-form artifact. Material limitations or hypotheses must remain identifiable after compression into the summary, mechanics, diagram, and audit trail.

## Existing repository checks

Run from repository root with the Python dependencies already used by the project:

```sh
python scripts/analyze_ecosystem.py model/ai_ecosystem.yaml assurance --json
python scripts/validate_ecosystem.py model/ai_ecosystem.yaml schema/ai_ecosystem_schema.yaml --refs docs/inquiries/inq-standards-certification-efficiency.md
```

The assurance analyser tests graph reachability and selected authority relationships; it does **not** establish legal effect, evaluator independence, or the correctness of a language-model explanation. The reference validator checks identifiers and some textual node-pair claims; successful execution does **not** prove that a published inquiry's broader conclusions are sound.

## Acceptance and non-goals

The protocol passes this case when the generated inquiry preserves existing graph facts, makes material assumptions and unsupported conclusions visible, and identifies a bounded, testable gap **only where needed**. An answer claiming complete assurance merely because a directed path reaches `N_AUDITOR` fails. An answer claiming there is no route for behavioural evidence to reach `N_AUDITOR` also fails on the current model.

This check does not assert that the scenario has been replayed in a specific LLM environment. It does not change the canonical ontology, propose a certification-state API, or establish any external legal conclusion. A future machine check should be justified by failures observed in actual generated inquiries, not introduced solely because this scenario exists.
