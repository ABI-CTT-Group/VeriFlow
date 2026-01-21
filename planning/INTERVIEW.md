# Flow Interview: VeriFlow Spec Generation

This document corresponds to the ongoing interview process to generate a comprehensive `spec.md` for VeriFlow.

## Round 1: Core Architecture & Scope

**Q1. Codebase Status**
I see a Vite project in `planning/UI`. Is this the active codebase we will be building upon for the frontend, or is it just a reference prototype?

**A1.** Just a reference prototype. We will build the actual frontend from scratch (or structure it properly) based on the PRD, using this as a visual reference if needed.

---

**Q2. Backend Architecture**
The PRD mentions Apache Airflow 3 for execution. 
- Will there be a dedicated backend API (e.g., FastAPI, Django, Node.js) to serve the UI and orchestrate the agents?
- Or will the UI communicate directly with Airflow and the Agents?

**A2.** Dedicated backend API using **FastAPI**. It will serve the UI and act as the orchestrator/interface for Airflow.

---

**Q3. Agent Framework**
For the "Scholar", "Engineer", and "Reviewer" agents (powered by Gemini 3):
- Do you have a preferred framework? (e.g., LangChain, Google GenAI SDK, Semantic Kernel, etc.)
- Where will this agent logic reside?

**A3.** **Recommendation:** We will use **PydanticAI** (or LangGraph). 
*Reasoning:* You chose FastAPI, and PydanticAI integrates perfectly with it. It enforces strict typing on Agent outputs, which is critical for "Verifying" workflows and generating valid CWL/SDS structures. 
*Decision:* Proceeding with PydanticAI unless you object.

---

**Q4. Scope definition**
For this immediate task, what is the boundary of "Done"?
- Are we scaffolding the entire system (UI + Backend + Agents + Airflow setup)?
- Or are we focusing on specific components (e.g., just the UI implementation of the PRD)?

**A4.** **Entire System**: UI + Backend (FastAPI) + Agents (Gemini) + Airflow 3 setup.

---

**Q5. Data Persistence**
The PRD mentions a "Catalogue Module" and preserving state. 
- How should data be stored? (SQLite, PostgreSQL, local JSON files / SDS structure?)
- Does the "Dataset Navigation Module" imply a local file system view or an abstracted storage layer?

**A5.** **See Round 1.5 below for Options.**

---

**Q6. Infrastructure**
- Is the target environment for this MVP a local setup (e.g., via Docker Compose) or a cloud deployment?
- Do you already have Airflow 3 set up, or does that need to be part of the build?

**A6.** **Cloud Deployment** on ARDC Nectar Research Cloud. This implies we should containerize everything (Docker Compose for dev, potentially Kubernetes or Docker Swarm/Compose for prod) to run on Nectar VMs.

---

## Round 1.5: Data Persistence Options (Follow-up to Q5)

You asked for options for storing state information. Given the requirement for "Scientific Reproducibility" and deployment on "ARDC Nectar" (likely Virtual Machines), here are the options:

**Option A: The "Integrity" Stack (Recommended)**
- **Database:** **PostgreSQL** (with `pgvector` extension).
    - Stores Users, Project Metadata, Run History, and Vector Embeddings for the "Scholar" agent.
    - *Why:* Airflow *requires* a SQL database (Postgres is best). Using one DB for both Airflow and App is efficient.
- **Object Storage:** **MinIO** (Self-hosted S3 compatible).
    - Stores the heavy PDF files, extracted Images, and the specific SDS directory structures.
    - *Why:* S3 API is the industry standard. MinIO runs easily in Docker on Nectar.

**Option B: The "NoSQL" Stack**
- **Database:** **MongoDB** or **FerretDB**.
    - Stores JSON-like documents (flexible ISA structures).
    - *Why:* Good if the schema changes rapidly.
    - *Cons:* Airflow still needs a SQL DB, so you'd end up maintaining *two* databases (Postgres for Airflow, Mongo for App).

**Decision:** **Option A (Postgres + MinIO)** selected.

---

## Round 2: Tech Stack & Integrations

**Q7. Frontend Framework**
The reference prototype is Vite.
- Shall we stick to **React + TypeScript + Vite**?
- Any specific component library preference? (e.g., **Shadcn/UI** + **Tailwind** is modern and fits the "Clean/Modular" PRD requirement).

**A7.** **Vue 3 + TypeScript + Vite + Tailwind.**
- Reference `docs/UI.png` and `docs/UI` folder for style.
- *Visual Style:* The "Workflow Assembler" should look/feel like **ComfyUI** (see reference image).

**Q8. Airflow Integration**
Airflow 3 is cutting edge.
- Will the "Engineer Agent" generate Python DAG files and push them to a git repo that Airflow syncs? 
- OR will we use the Airflow REST API to trigger generic DAGs with dynamic parameters?

**A8.** **CWL -> DB -> Airflow conversion.**
- "Engineer" defines Tools/Workflows in **CWL** (Source of Truth).
- stored in Internal Database (SDS structure).
- "Engineer" converts CWL -> Airflow DAG -> Sent to Airflow (which is packaged within VeriFlow).

**Q9. Visualizing Workflows (react-flow?)**
The PRD mentions a "Workflow Assembler Module".
- Can we use **React Flow** (or XYFlow) for the visual graph editor?

**A9.** User suggested **ComfyUI UX** + **Vue Flow**. 
- *Clarification:* "ComfyUI" is a full app, but we will likely use **Vue Flow** to *replicate* the ComfyUI node-graph experience (typed ports, wires, dark theme).
- *Redundancy:* Using actual ComfyUI frontend code inside a generic Vue app is difficult/redundant. **Vue Flow** is the correct library to build the *Comfy-like* interface.

**Q10. Authentication**
- Do we need multi-user support for the MVP?
- If yes, simple email/password (managed by FastAPI/DB) or an external provider (OAuth/Google)?

**A10.** **Single User for MVP.**
- Auth in future.
- Gemini Key baked into server for now.
- State loading: Download/Upload state files (JSON/Zip) initially; DB storage later.

**Q11. PDF Parsing**
- For the "Scholar Agent", does it just pass the raw text to Gemini?
- Or should we use a specialized tool like `LlamaParse` or `unstructured.io` to handle tables/graphs in scientific papers better?

**A11.** **Pass raw to Gemini.**

---

## Round 3: Detailed Logic & Execution

**Q12. Workflow UX Details (ComfyUI Style)**
You provided a ComfyUI screenshot. To be clear:
- You want the *visual style* (dark inputs, curved colored wires, execution nodes)?
- Do you need the complex "custom node" definition UI of ComfyUI, or just a fixed set of "Tool" nodes that populate from the database?

**A12.** **ComfyUI Mechanics + VeriFlow Theme.**
- **Mechanics:** Complex "custom node" definition IS required (ports, resizing, etc.).
- **Data Source:** Node definitions populated from "Scholar" findings (extracted measurements/tools).
- **Theme:** Match `docs/UI.png` (VeriFlow theme), NOT default ComfyUI style.

**Q13. Execution Trigger**
When the user clicks "Run" in the UI:
- Does the Backend generate the *entire* Airflow DAG at that moment and push it?
- Does it wait for Airflow to acknowledge before showing "Running"?

**A13.** **Immediate DAG Generation.**
- "Run" -> Backend converts CWL to DAG -> Pushes to Airflow.
- UI waits for Airflow "Running" status before updating.

**Q14. Docker Building**
The PRD says Agent B (Engineer) generates Dockerfiles.
- Does VeriFlow need to *build* these images? (i.e., do we need access to a Docker daemon to run `docker build`?)
- Or do we just generate the text of the Dockerfile for the user to use later?
- *Assumption:* To run "on the paper's original data" (Execution), we must build the image.

**A14.** **Active Docker Build.**
- "Engineer" generates Dockerfile text -> **Builds** image using Docker Daemon.
- Requirement: Access to `/var/run/docker.sock` or remote Docker host.

**Q15. Agent Memory/Context**
- Since we are passing raw PDF to Gemini, are we relying on Gemini 3 Pro's large context window?
- Do we need persistent "Agent Memory" (vector DB) for anything other than the PDF content? (You mentioned `pgvector` in Option A, so clarifying its use).

**A15.** **Persistent Memory + Model Switching.**
- Default: Gemini 3 Pro (large context).
- Configurable models per agent.
- Persistent Memory (pgvector): Used for confidence metrics, past decisions, citation linking (not just PDF content).

---

## Interview Complete

Proceeding to generate `planning/spec.md`.
