

Product Requirements Document (PRD): VeriFlow

Project Title: VeriFlow (The Verifiable Workflow Architect)

Target Release: MVP (Hackathon Phase)

Date: January 15, 2026

1\. Executive Summary

VeriFlow is an autonomous "Research Reliability Engineer" designed to solve the crisis of non-replicable science. By utilizing Gemini 3 to ingest scientific publications, VeriFlow automates the creation of verifiable, executable research workflows. It extracts methodological logic, verifies code repositories, and packages tools into Common Workflow Language (CWL) descriptions. These are executed using Apache Airflow 3, maintaining strict data interoperability via the SPARC Dataset Structure (SDS) and the ISA Framework. The MVP allows a researcher to upload a PDF, visualize the study design, and verify the workflow by executing it on the paper's original data.

2\. User Personas

 \* The Replication Researcher (Primary): Wants to verify the results of a paper before building upon them. Needs to run the author's code on the author's data without debugging dependency issues.

 \* The Methodologist: Wants to inspect the exact logic of a study's workflow to understand how data flowed from input to result.

 \* The Data Curator: Needs to organize unstructured research outputs into standardized, FAIR-compliant datasets (SDS) for archival.

3\. UI/UX Requirements

3.1 General Interface Guidelines

 \* Design Philosophy: Minimalistic, modular, and clean. Only Hackathon examples (e.g., Breast Cancer Segmentation) should be used for design validation.

 \* Modularity: All modules must be collapsible, and their borders must be adjustable (resizable).

 \* Layout Constraint: To support drag-and-drop workflows, the Upload Module, Catalogue Module, and Workflow Assembler Module must be co-located on the same view.

 \* Configuration & State:

   \* Re-analysis Trigger: Users must be able to configure whether the Scholar Agent re-analyses the paper automatically upon property edits or manually via a button.

   \* State Preservation: The system must track user-edited properties to ensure the Scholar Agent does not overwrite manual inputs during re-analysis.

 \* Export:

   \* Node Export: Ability to download the SDS associated with any specific node at any time.

   \* Global Export: Feature to download the entire project package.

3.2 Module Specifications

1\. Upload Module

 \* Function: Accepts uploads of the primary PDF paper and associated files (code, supplementary data).

2\. Catalogue Module

 \* Function: A dynamic repository of extracted Data Objects.

 \* Features:

   \* Automatically populates as objects are discovered.

   \* Descriptions update dynamically if edited elsewhere.

   \* Objects separated by collapsible/scrollable panels (Measurements, Tools, Models).

   \* Supports drag-and-drop into Study Design and Workflow modules.

3\. Property Editor Module

 \* Function: Context-sensitive editor for node attributes.

 \* Interaction: Triggered by clicking a node in the Study Design or Workflow Assembler modules. Shows properties specific to that node type.

4\. Console Module

 \* Function: Communication hub.

 \* Features:

   \* Chat interface with VeriFlow agents.

   \* Timestamped logs showing agent actions and progress.

5\. Study Design Selector Module

 \* Function: Visualizes the extracted ISA (Investigation, Study, Assay) hierarchy.

 \* Nodes:

   \* Paper Node: Root node with name property.

   \* Investigation/Study Nodes: Editable description properties.

   \* Assay Nodes: Contain multiple numbered properties for sequential workflow steps.

 \* Editing: Users can edit, remove, add, or insert steps (with Undo functionality).

 \* Selection: User selects the specific Assay to assemble.

6\. Workflow Assembler Module

 \* Function: Visual canvas for the computational pipeline (Flow: Left \\rightarrow Right).

 \* Structure:

   \* Input Measurement Node (Left): Defines Dataset/Sample pairs. Auto-populated but editable.

   \* Tool Nodes (Center): Multiple inputs/outputs. Unused ports are hidden.

   \* Model Nodes: Similar to measurements but link single model properties to tools.

   \* Output Measurement Node (Right): Defines destination for results.

 \* Interaction:

   \* "Plus" Button: Allows adding/re-ordering inputs/outputs via dropdown (Scholar-identified values) or custom entry (manual definition).

 \* Execution Controls:

   \* Subject Specification: Field to specify the number of subjects to run (subsetting the total available).

   \* Run/Abort: "Run All", "Re-run" (individual tools), and "Abort" buttons.

   \* Status: Visual indicators and icons on nodes (provided by Reviewer Agent) showing status and confidence scores.

   \* Diagnostics: Integration with Airflow API for status updates; link provided to external Airflow Dashboard.

7\. Dataset Navigation Module

 \* Function: Explorer for the SDS directory tree.

 \* Features: Navigation of folders; syntax highlighting for metadata/code files.

8\. Plugins Module

 \* Function: Extensibility framework.

 \* Interaction: Registers context-menu actions (right-click) in the Dataset Navigation Module.

   \* Example: Selecting a text file offers a text editor; selecting a 3D image offers the VolView panel.

4\. Functional Requirements

4.1 Stage 1: Workflow Description Templating

 \* FR 1.1: Ingestion & Extraction

   \* Agent A (Scholar) must parse the uploaded PDF to identify the Investigation, Study, and Assay hierarchy.

   \* System must auto-populate the Study Design Selector and Catalogue modules.

 \* FR 1.2: User Selection

   \* User must select specific Assays for replication.

   \* System must generate SDS metadata for Assays and Studies based on this selection.

 \* FR 1.3: Subject Limiting (Configuration)

   \* System must identify the total number of subjects in the paper.

   \* User must be able to limit the execution to a specific number of subjects (e.g., "Run on first 3 subjects only") via the Workflow Assembler. Default is Subject 1\.

4.2 Stage 2: Workflow Execution Templating

 \* FR 2.1: Graph Population

   \* Upon Assay selection, Scholar Agent must populate the Workflow Assembler with Input, Tool, Model, and Output nodes.

 \* FR 2.2: Tool Containerization

   \* Agent B (Engineer) must scan the code repository, infer dependencies, and generate Dockerfiles wrapped in CWL.

 \* FR 2.3: Input/Output Configuration

   \* System must expose inputs/outputs on Tool nodes.

   \* User must be able to map Measurement SDS (Datasets/Samples) to these inputs using the Property Editor or the "Plus" button menus.

 \* FR 2.4: Adapter Generation

   \* Agent B must check MIME-types (additional\_type) of connected nodes.

   \* If mismatches exist (e.g., DICOM vs NIfTI), Agent B must auto-generate and inject "Adapter Tools" into the workflow.

4.3 Stage 3: Workflow Execution and Diagnostics

 \* FR 3.1: Execution Orchestration

   \* System must convert the visual CWL representation into Apache Airflow 3 DAGs.

   \* System must iterate the workflow for the number of subjects specified by the user.

 \* FR 3.2: Live Monitoring

   \* Agent C (Reviewer) must query the Airflow API to update visual status icons on the Workflow nodes.

   \* Logs must be displayed in the Console Module.

 \* FR 3.3: Error Handling

   \* If a tool fails, Agent C must analyze the stack trace and provide natural language advice in the Console.

4.4 Stage 4: Workflow Results Review

 \* FR 4.1: Provenance Linking

   \* System must create a Derived Measurement SDS for outputs.

   \* Metadata must link outputs to inputs, tools, and the workflow version used via wasDerivedFrom.

 \* FR 4.2: Visualization

   \* User must be able to browse results in the Dataset Navigation Module.

   \* System must trigger appropriate plugins (e.g.,  VolView) based on file type.

5\. Data Standardization Strategy

5.1 Data Objects (SDS)

 \* Measurement SDS: Contains raw data (subjects/samples).

 \* Model SDS: Similar to measurement but contains no subjects or samples. Pre-trained weights are stored in the primary/ folder.

 \* Tool SDS: Contains executable code and Dockerfiles.

 \* Workflow SDS: Contains CWL definitions.

 \* Context SDS: Contains ISA metadata.

5.2 Standardization Rules

 \* One Assay \= One Workflow: Each Assay node corresponds to exactly one Workflow definition.

 \* CWL as Source of Truth: All Tools and Workflows are described internally in CWL to ensure engine independence.

 \* MIME-Typing: All files must include additional\_type metadata to facilitate the Engineer Agent's automated type-checking and adapter generation.

6\. System Agents (The Triad)

 \* Agent A: The Scholar: Handles literature parsing, ISA extraction, and metadata population. Active in Stage 1\.

 \* Agent B: The Engineer: Handles code analysis, dependency inference, Docker/CWL generation, and dynamic adapter creation. Active in Stage 2\.

 \* Agent C: The Reviewer: Handles validation, log analysis, error translation, and confidence scoring. Active throughout all stages.