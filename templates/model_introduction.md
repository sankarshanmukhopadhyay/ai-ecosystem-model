# AI Ecosystem: Multi-Lens Architecture & Governance

## Welcome to Sezoo's **AI Ecosystem Model**

This model is an interactive conceptual map designed to help decision-makers, architects, and regulators explore and make sense of the global AI ecosystem. 

Most analyses view AI through a single, isolated lens: engineers focus on model weights and APIs; economists analyze CapEx and subscription margins; lawyers debate liability regimes; and safety researchers evaluate model alignment. In reality, these domains are connected by explicit and implicit relationships. There is no hierarchy in these relationships - no view is "superior" to the other, but there are side-effects and consequences. Pulling one thread can affect many others, and sometimes with unexpected consequences. 

Our goal with this model is to balance **sufficient conceptual richness with sufficient visual simplicity**. Providing a map rigorous enough to stress-test real-world decisions, yet clear enough to build shared understanding. Two favourite quotes/sayings have been front of mind during the development:

> *"All models are wrong, but some are useful."* — George Box

> *"A model is only useful **because** it simplifies reality"* - Borges' Map

---

## The Theoretical Foundations

The model uses four frameworks to create a single, machine readable property graph:

### 1. Cybernetic Control: Stafford Beer’s Viable System Model (VSM)
Traditional governance models rely on static organizational charts. In contrast, Beer’s VSM[^1] assesses whether a system possesses the operational variety and regulatory feedback required to remain **viable** under dynamic (changing) conditions. The model divides an organization into two main halves: System 1 (\"S<sub>1</sub>\", Operations), which does the primary work, and Systems 2–5 (\"S<sub>2-5</sub>\", the Meta-System), which coordinate, control, plan, and govern the whole enterprise. Two other key concepts are recursion: a viable system is considered a fractal; and algedonic signals, emergency alert channels.  

* **Viewpoint-Relative Recursion:** VSM roles are not intrinsic node tags. An entity's role depends on the chosen system-in-focus. We model two primary recursion levels:
  * **Level 0 (Enterprise AI Operations):** How an enterprise balances autonomous agent operations (*S<sub>1</sub>*) through coordination (*S<sub>2</sub>*), policy kernels and audit stores (*S<sub>3</sub>*), risk intelligence (*S<sub>4</sub>*), and executive direction (*S<sub>5</sub>*).
  * **Level +1 (Societal & Jurisdictional Governance):** How global markets (*S<sub>1</sub>*), standards bodies (*S<sub>2</sub>*), regulators and courts (*S<sub>3</sub>*), safety institutes (*S<sub>4</sub>*), and legislature (*S<sub>5</sub>*) maintain macro-societal viability.
* **The Algedonic Channel:** A dedicated emergency tripwire that bypasses intermediate bureaucratic layers (*S<sub>3</sub>*) directly to ultimate policy closure (*S<sub>5</sub>*) when critical failures or systemic harms occur.

### 2. Value Chains & Capital Constraints: Simon Wardley’s Evolution Mapping
Components in the AI stack do not share the same economic properties. We track the evolution of value-chain components using a Wardley Maps[^2] scale from from **Genesis** → **Custom-Built** → **Product** → **Commodity**:
* **Physical & Capital Chokepoints:** Photolithography equipment (ASML EUV) and leading-edge semiconductor packaging (TSMC CoWoS) remain rare, highly centralized capital assets with multi-year construction lead times and *prohibitive* switching costs.
* **Artificial Lock-In on Utilities:** Cloud compute and raw storage are commodity utilities, yet hyperscalers construct artificial switching costs through egress fees, proprietary IAM meshes, and bundled foundation models.

**Note:** There is significant scope to further develop the use of the Wardley Map evaluation in the model, but we think this is best done as a worked use-case exercise. At present we have ensured that the model *can* represent Wardley Map maturity. 

### 3. Non-Linear Feedback Dynamics (Jay Forrester & Donella Meadows)
Donella Meadows added value to Jay Forrester's earlier work[^3] and their work encouraged us to include the observation that the AI ecosystem includes non-linear delays and feedback loops. For example:
* **Reinforcing Flywheels (*R<sub>1</sub>*):** Capital markets subsidize training compute, producing frontier capability and valuation uplift, which in turn attracts more capital, driving extreme market concentration.
* **Balancing Brakes (*B<sub>1</sub>*–*B<sub>4</sub>*):** Open-weight model releases compress commercial inference margins (*B<sub>1</sub>*), while real-world blast radius harms trigger regulatory penalties, social-licence revocation, and legislative intervention (*B<sub>2</sub>*–*B<sub>4</sub>*).

### 4. Computable Schema & Referential Integrity (LinkML)
Early iterations of this model used a stand-alone data model instance "loosely" defined in YAML. As we evolved our thinking we abstracted the schema from the model instance and introduced a more formal (LinkML) structure for the schema (expressed using YAML). 

The current model is built on a structured blueprint (`ai_ecosystem_schema.yaml`). Before any diagrams or web pages are created, every component, connection, system complexity level, and legal requirement is automatically checked against strict rules to make sure it fits together properly.

---

## Exploring the Model

### Interactive Ecosystem Explorer

Use the interactive viewer below to explore the global model. You can switch between thematic views, isolate specific domains (Economic, Governance, Technical), run standing inquiries, or click any node to inspect its cardinality, Ashby variety, and VSM roles:

<div style={{ position: 'relative', width: '100%', height: '620px', marginBottom: '24px' }}>
  <iframe
    src="/viewer/?view=all" 
    width="100%" 
    height="100%" 
    style={{ border: '1px solid #282d3c', borderRadius: '8px', backgroundColor: '#14161d' }} 
    title="AI Ecosystem Interactive Model Viewer"
  ></iframe>
</div>

*(Tip: You can also toggle the **Matrix** tab in the viewer toolbar to inspect cluster connectivity and gap analysis).*

You can see a whole page version of this here: https://ai-ecosystem.sezoo.digital/viewer/

---

## How to Use the Model for Sense-Making

### 1. Review Pre-Computed Inquiries
We have pre-computed analytical investigations into core strategic questions across the stack. These include:
* **[Physical & Geopolitical Chokepoints](./inquiries/inq-physical-geopolitical-chokepoints.md):** Where power concentrates and single points of failure reside.
* **[Macroeconomics & Valuations](./inquiries/inq-ai-economics-valuations.md):** How CapEx cycles, token deflation, and open-weight commoditization interact.
* **[Public Trust & Liability](./inquiries/inq-public-trust-and-social-acceptance.md):** Where recourse breaks when autonomous systems cause downstream harm.
* **[Standards & Certification](./inquiries/inq-standards-certification-efficiency.md):** How voluntary standards attenuate technical variety into compliance baselines.
* **[Continuing Assurance](./inquiries/inq-continuing-assurance.md):** How approvals remain trustworthy as systems drift and how permissions are revoked.

Visit the **[Sense-Making Inquiries](./inquiries)** section to explore the full library.

### 2. Formulate a New Line of Inquiry
You can use the model to evaluate novel policy questions, architectural changes, or strategic investments using an LLM-assisted workflow:

1. **Select an LLM Environment:** Open your environment of choice (e.g. Claude, Google AI Studio, ChatGPT).
2. **Load the Protocol:** Provide the system instructions from `prompts/inquiry_protocol.md`.
3. **Provide Context:** Attach the canonical model file `model/ai_ecosystem.yaml` (if your interface has trouble with file attachments, paste the YAML content enclosed in triple backticks).
4. **Explore Conversationally:** Interrogate the graph (e.g., *"What happens to systemic viability if independent safety institutes are removed?"* or *"How does token deflation affect ISV application margins?"*).
5. **Draft & Contribute:** Prompt the AI to *"Draft the inquiry artifact following the Sezoo inquiry template"*, verify the referential integrity using `validate_ecosystem.py --refs`, and submit a Pull Request to our GitHub repository.

**Note:** We anticipate that inquries may identify gaps and / or opportunities to improve the model. Suggestions on model improvement supported by justifications and explanations are welcome. 

---

## Canonical Model Sources & Visual Exports

The complete, computable representation is maintained in our open repository:
* **Metamodel Schema:** [`schema/ai_ecosystem_schema.yaml`](https://raw.githubusercontent.com/sezoo-digital/ai-ecosystem-model/refs/heads/main/schema/ai_ecosystem_schema.yaml)
* **Model Instance:** [`model/ai_ecosystem.yaml`](https://raw.githubusercontent.com/sezoo-digital/ai-ecosystem-model/refs/heads/main/model/ai_ecosystem.yaml)

Below, the master architecture is documented via static visual keys, feedback loops, VSM frame assignments, and the complete element dictionary.

[^1]: There are many sources and books on VSM, this is the wikipedia entry: https://en.wikipedia.org/wiki/Viable_system_model 

[^2]: There are many places to learn about Simon Wadley Maps, here's one: https://www.wardleymaps.com/guides/wardley-mapping-101

[^3]: Meadows, D. H. (2008). Thinking in systems: A primer (D. Wright, Ed.). Chelsea Green Publishing.