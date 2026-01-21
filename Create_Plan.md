Given **PRD.md**, **spec.md**, **Proposal.md**  in markdown, all the files in the **UI** folder.

## Requirements for PLAN.md

### 1. Overview
- Summarize the system goals, non-goals, and key assumptions inferred from the documents.
- List any ambiguities or open questions first. If unresolved, proceed with clearly stated assumptions.

### 2. Development Stages
- Break development into clear, sequential stages or milestones.
- For each stage, define explicit entry criteria and exit criteria.

### 3. Tasks per Stage
- For each stage, list detailed tasks assigned to:
  - **AI (the agent)**
  - **Developer (the human)**
- Minimize tasks assigned to the Developer. Limit them to external setup, credentials, approvals, or brief validation steps.
- Include task dependencies where relevant.

### 4. Testing Plan per Stage
- For every stage, include a concrete testing plan covering:
  - Unit tests
  - Integration tests
  - End-to-end tests using Playwright mapped to critical user flows
- All primary testing must be performed by you. This includes writing tests, running them, fixing all discovered bugs, and re-running tests until they pass.
- You may assign Developer a small number of final validation or sanity-check tasks, but only after your full test suite passes.

### 5. Quality Gates
- Define what “stage complete“ means. For example:
  - All tests passing
  - No known critical or high-severity bugs
  - Demo flow verified end-to-end by AI

### 6. Risks and Mitigations
- Identify technical or product risks per stage and how they will be mitigated or tested.

### 7. Final Review and Handoff
- Describe the final verification steps you will perform before asking Developer for sign-off.
- Include a short checklist I can use to confirm readiness.

The output should be a single, well-structured **PLAN.md** with actionable detail. Avoid vague language. Prefer concrete tasks, explicit test cases, and clear completion criteria.
