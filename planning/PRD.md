Product Requirements Document (PRD): VeriFlow
Project Title: VeriFlow (The Verifiable Workflow Architect)
Target Release: MVP (Hackathon Phase)
Date: January 15, 2026
1. Executive Summary
VeriFlow is an autonomous "Research Reliability Engineer" designed to solve the crisis of non-replicable science. By utilizing Gemini 3 to ingest scientific publications, VeriFlow automates the creation of verifiable, executable research workflows. It extracts methodological logic, verifies code repositories, and packages tools into Common Workflow Language (CWL) descriptions. These are executed using Apache Airflow 3, maintaining strict data interoperability via the SPARC Dataset Structure (SDS) and the ISA Framework. The MVP allows a researcher to upload a PDF, visualize the study design, and verify the workflow by executing it on the paper's original data.
2. User Personas
 * The Replication Researcher (Primary): Wants to verify the results of a paper before building upon them. Needs to run the author's code on the author's data without debugging dependency issues.
 * The Methodologist: Wants to inspect the exact logic of a study's workflow to understand how data flowed from input to result.
 * The Data Curator: Needs to organize unstructured research outputs into standardized, FAIR-compliant datasets (SDS) for archival.
3. UI/UX Requirements
3.1 General Interface Guidelines
 * Design Philosophy: Minimalistic, modular, and resizable. Only Hackathon examples (e.g., Breast Cancer Segmentation) should be used for design validation.
 * Layout Layout:
   * Left Panel: Upload and Study Design.
   * Center Panel: Workflow Assembler, Catalogue, and Viewer.
   * Right Panel: Visualise and Export Results.
   * Bottom Panel: Console.
 * State Persistence: UI state (e.g., expanded/collapsed panels, PDF URL) persists across operations.
 * Visual Coding:
   * Blue: Measurement Nodes.
   * Purple: Tool Nodes.
   * Green: Model Nodes.
3.2 Module Specifications
1. Upload Publication Module (Left Panel)
 * Function: Drag-and-drop file upload (PDF/ZIP/Code).
 * Behavior: Auto-collapses after successful upload to reveal Study Design.
2. Review Study Design Module (Left Panel)
 * Function: Tree structure display of Study, Subjects, and Assays with confidence scores.
 * Actions:
   * Click [source] to open Viewer Panel.
   * Select Assay to enable "Assemble Workflow" button.
   * "Assemble Workflow" collapses Left Panel and populates Center Canvas.
3. Workflow Assembler Module (Center Panel)
 * Default State: Always visible.
 * Sub-components:
   * Workflow Canvas: Visual graph editor for dragging and connecting nodes.
     * Nodes: Measurement (Blue), Tool (Purple), Model (Green).
     * Interaction: Drag output port to input port to connect.
   * Data Object Catalogue: Tree view of inputs/outputs (Measurements/Datasets).
   * Viewer Panel: Displays PDF citations via plugins (Auto, PDF.js, Embed).
4. Visualise and Export Results Module (Right Panel)
 * Function: File tree viewer for exploring results.
 * Behavior: Auto-expands when workflow runs. Filters file tree based on selected workflow node.
5. Console Module (Bottom Panel)
 * Function: Real-time logging of execution, errors, and status.
 * Behavior: Resizable top border.
4. Functional Requirements
4.1 Stage 1: Workflow Description Templating
 * FR 1.1: Ingestion & Extraction
   * Agent A (Scholar) must parse the uploaded PDF to identify the Investigation, Study, and Assay hierarchy.
   * System must auto-populate the Review Study Design Module.
 * FR 1.2: User Selection
   * User must select specific Assays for replication.
   * System must generate SDS metadata for Assays and Studies based on this selection.
 * FR 1.3: Subject Limiting (Configuration)
   * System must identify the total number of subjects in the paper.
   * User must be able to limit the execution to a specific number of subjects via the interface.
4.2 Stage 2: Workflow Execution Templating
 * FR 2.1: Graph Population
   * Upon Assay selection, Scholar Agent must populate the Workflow Canvas with Measurement, Tool, and Model nodes.
 * FR 2.2: Tool Containerization
   * Agent B (Engineer) must scan the code repository, infer dependencies, and generate Dockerfiles wrapped in CWL.
 * FR 2.3: Input/Output Configuration
   * System must expose inputs/outputs on Tool nodes.
   * User must be able to map Measurement SDS (Datasets/Samples) to these inputs.
 * FR 2.4: Adapter Generation
   * Agent B must check MIME-types (additional_type) of connected nodes and inject "Adapter Tools" if mismatches exist.
4.3 Stage 3: Workflow Execution and Diagnostics
 * FR 3.1: Execution Orchestration
   * System must convert the visual CWL representation into Apache Airflow 3 DAGs.
   * System must iterate the workflow for the number of subjects specified by the user.
 * FR 3.2: Live Monitoring
   * Agent C (Reviewer) must query the Airflow API to update visual status icons (Pending/Running/Completed/Error) on the Workflow nodes.
   * Logs must be displayed in the Console Module.
 * FR 3.3: Error Handling
   * If a tool fails, Agent C must analyze the stack trace and provide natural language advice in the Console.
4.4 Stage 4: Workflow Results Review
 * FR 4.1: Provenance Linking
   * System must create a Derived Measurement SDS for outputs.
 * FR 4.2: Visualization
   * User must be able to browse results in the Visualise and Export Results Module.
   * Selecting a dataset in a measurement node highlights it in the file tree.
5. Data Standardization Strategy
5.1 Data Objects (SDS)
 * Measurement SDS: Contains raw data (subjects/samples).
 * Model SDS: Similar to measurement but contains no subjects or samples. Pre-trained weights are stored in the primary/ folder.
 * Tool SDS: Contains executable code and Dockerfiles.
 * Workflow SDS: Contains CWL definitions.
 * Context SDS: Contains ISA metadata.
5.2 Standardization Rules
 * One Assay = One Workflow: Each Assay node corresponds to exactly one Workflow definition.
 * CWL as Source of Truth: All Tools and Workflows are described internally in CWL to ensure engine independence.
 * MIME-Typing: All files must include additional_type metadata to facilitate the Engineer Agent's automated type-checking and adapter generation.
6. System Agents (The Triad)
 * Agent A: The Scholar: Handles literature parsing, ISA extraction, and metadata population. Active in Stage 1.
 * Agent B: The Engineer: Handles code analysis, dependency inference, Docker/CWL generation, and dynamic adapter creation. Active in Stage 2.
 * Agent C: The Reviewer: Handles validation, log analysis, error translation, and confidence scoring. Active throughout all stages.
