# VeriFlow - Research Reproducibility Engineer

## Overview

VeriFlow is an autonomous "Research Reproducibility Engineer" designed to solve the crisis of non-replicable science by using AI agents to ingest scientific publications, extract methodological logic, and create verifiable, executable research workflows.

The system uses three specialized AI agents (Scholar, Engineer, Reviewer) that work with standardized data objects following the SPARC Dataset Structure (SDS) and ISA Framework, with workflows described in Common Workflow Language (CWL) and executed via Apache Airflow.

## Core Principles

### Design Philosophy
- **Minimalistic & Modular**: All modules are collapsible and resizable
- **Drag-and-Drop Workflows**: Visual workflow assembly between components
- **State Persistence**: UI state persists across panel collapse/expand operations
- **Logical Progression**: Upload → Study Design → Workflow Assembly → Dataset Navigation

### Standards Compliance
- **SPARC Dataset Structure (SDS)**: Standardized data organization
- **ISA Framework**: Investigation, Study, Assay metadata structure
- **Common Workflow Language (CWL)**: Workflow description format
- **Apache Airflow**: Workflow execution engine

## System Architecture

### Three AI Agents
1. **Scholar Agent**: Ingests publications, extracts methodological logic
2. **Engineer Agent**: Converts methods to executable workflows
3. **Reviewer Agent**: Validates workflow reproducibility

### Data Objects
- Input/output measurement nodes are collections of individual measurement datasets
- Consistent naming across workflow nodes, data object catalogue, and file tree viewer
- Datasets identified by Scholar or manually added by user

## User Interface Structure

### Layout Overview
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: VeriFlow - Research Reproducibility Engineer       │
├──────────┬──────────────────────────────┬───────────────────┤
│          │                              │                   │
│  LEFT    │    WORKFLOW ASSEMBLER        │  RIGHT PANEL      │
│  PANEL   │    (Center)                  │  (Collapsible)    │
│          │                              │                   │
│  1. Upload│   - Workflow Canvas         │  4. Visualise &   │
│  2. Study│   - Data Object Catalogue    │     Export        │
│     Design│   - Viewer Panel            │     Results       │
│          │   3. Assemble Workflow       │                   │
│          │                              │                   │
├──────────┴──────────────────────────────┴───────────────────┤
│ CONSOLE (Resizable, Collapsible)                            │
└─────────────────────────────────────────────────────────────┘
```

## Module Specifications

### 1. Upload Publication Module (Left Panel)

**Location**: Top of left panel  
**Default State**: Expanded initially, collapses after upload  
**Persistence**: Starts collapsed when reopening left panel if files uploaded

#### Features
- Drag-and-drop file upload
- Browse file selection
- File type support: PDF, ZIP, code repositories
- File list with remove capability
- Auto-collapse after successful upload

#### State Management
- Files stored in local component state
- PDF URL lifted to App.tsx for persistence
- `hasUploadedFiles` derived from `uploadedPdfUrl`

#### Visual Indicators
- File count display
- Upload status feedback

---

### 2. Review Study Design Module (Left Panel)

**Location**: Bottom of left panel  
**Default State**: Collapsed initially, expands after upload  
**Persistence**: Starts expanded when reopening left panel if files uploaded

#### Features
- Tree structure display of research study
- Expandable/collapsible nodes
- Source citation with confidence scores
- Assay selection for workflow assembly
- "Assemble Workflow" action button

#### Tree Structure
```
Study
├── subjects (properties)
│   ├── Property 1 [source] [confidence]
│   └── Property 2 [source] [confidence]
└── assays
    ├── Assay 1
    │   ├── Inputs
    │   │   └── Measurement datasets
    │   ├── Samples
    │   └── Outputs
    │       └── Measurement datasets
    └── Assay 2
        └── ...
```

#### Interactions
- Click [source] button → Opens PDF viewer with citation
- Select assay → Enables workflow assembly
- Click "Assemble Workflow" → Collapses left panel, creates workflow graph

#### State Management
- Selected assay tracked in App.tsx
- Expansion state initialized based on `hasUploadedFiles`
- PDF viewer state managed through callbacks

---

### 3. Workflow Assembler Module (Center Panel)

**Location**: Center of application  
**Default State**: Always visible (cannot be collapsed)

#### Sub-components

##### 3a. Workflow Canvas (Top)
**Purpose**: Visual workflow graph editor

**Features**:
- Node-based workflow visualization
- Drag-and-drop node positioning
- Connection lines between nodes
- Node status indicators (pending, running, completed, error)

**Node Types**:
1. **Measurement Nodes** (Input/Output)
   - Blue database icon
   - Container for dataset collections
   - Dataset/Sample selectors
   - Consistent naming with catalogue and file tree

2. **Tool Nodes**
   - Purple beaker icon
   - Processing steps
   - Input/output ports
   - Status indicators

3. **Model Nodes**
   - Green box icon
   - Model information
   - Configuration parameters

**Interactions**:
- Click node → Select for configuration/viewing
- Drag output port → Draw connection line
- Drop on input port → Create connection
- Click dataset in measurement node → Show in Dataset Navigation

**Connection Logic**:
- Drag from output port (right side)
- Drop on input port (left side)
- Visual feedback during drag
- Connection validation

**Workflow Actions**:
- Run Workflow button (top-right)
- Triggers workflow execution
- Updates node statuses
- Auto-expands Dataset Navigation panel

##### 3b. Data Object Catalogue (Middle Left)
**Purpose**: Browse and configure data objects

**Features**:
- Tree view of all data objects
- Expandable/collapsible sections
- Source citations with confidence
- Drag-and-drop to workflow canvas

**Structure**:
```
Data Objects
├── Inputs
│   ├── Measurement 1 [source] [confidence]
│   │   ├── Dataset 1
│   │   └── Dataset 2
│   └── Measurement 2
└── Outputs
    └── Measurement 3
```

**Interactions**:
- Click [source] → Open PDF viewer
- Expand/collapse sections
- Dataset names consistent with workflow nodes

##### 3c. Viewer Panel (Middle Right)
**Purpose**: Display PDF citations and documentation

**Features**:
- PDF viewer with citation highlighting
- Plugin system (auto, pdf.js, embed)
- Collapsible panel
- Close button
- Auto-expands on source click

**Viewer Plugins**:
1. **Auto**: Automatically selects best viewer
2. **PDF.js**: Custom PDF rendering
3. **Embed**: Native browser PDF viewer

**Behavior**:
- Opens when [source] button clicked
- Highlights relevant citation
- Can be manually collapsed
- Auto-collapses on workflow assembly

---

### 4. Visualise and Export Results Module (Right Panel)

**Location**: Right side of application  
**Default State**: Collapsed  
**Auto-expand**: When workflow runs

#### Features
- File tree viewer
- Dataset filtering by selected workflow node
- Dataset preview
- Export capabilities

#### File Tree Structure
```
MAMA-MIA/
├── primary/
│   └── DCE-MRI/
│       ├── Subject_001/
│       │   ├── T1w.nii.gz
│       │   └── metadata.json
│       └── Subject_002/
│           └── T1w.nii.gz
├── derivative/
│   └── segmentation/
│       ├── Subject_001/
│       │   └── tumor_mask.nii.gz
│       └── Subject_002/
│           └── tumor_mask.nii.gz
└── code/
    └── preprocessing/
        └── dcemri_process.py
```

#### Interactions
- Select workflow node → Filter file tree
- Select dataset in measurement node → Highlight in tree
- Expand/collapse folders
- File preview (future)
- Export options (future)

---

### Console Module (Bottom Panel)

**Location**: Bottom of application  
**Default State**: Expanded  
**Resizable**: Yes (drag top border)

#### Features
- Real-time workflow execution logs
- Status messages
- Error reporting
- Warning indicators
- Success confirmations

#### Log Categories
- System initialization
- File upload events
- Workflow assembly events
- Execution progress
- Completion status
- Error details

#### Resize Behavior
- Drag top border to resize
- Min height: 100px
- Max height: window height - 200px
- Smooth resize interaction

---

## User Flow

### Primary Workflow Path

#### 1. Upload Publication
```
User Action: Drag PDF to upload area or browse
System Response:
  - Upload module collapses
  - Study Design module expands
  - Scholar agent processes publication
  - Tree structure populated
```

#### 2. Review Study Design
```
User Action: Explore study tree, click [source] for citations
System Response:
  - PDF viewer opens on right
  - Citation highlighted
  - Confidence scores displayed
```

#### 3. Select Assay
```
User Action: Click assay in tree
System Response:
  - Assay highlighted
  - "Assemble Workflow" button enabled
```

#### 4. Assemble Workflow
```
User Action: Click "Assemble Workflow"
System Response:
  - Left panel collapses
  - Workflow canvas populated with nodes
  - Data Object Catalogue populated
  - Nodes positioned automatically
  - Connections drawn based on workflow logic
```

#### 5. Configure Workflow
```
User Action: 
  - Click nodes to select
  - Drag nodes to reposition
  - Draw connections between ports
  - Configure datasets in measurement nodes
System Response:
  - Node selection highlighting
  - Connection validation
  - Dataset dropdown population
```

#### 6. Run Workflow
```
User Action: Click "Run Workflow"
System Response:
  - Node statuses update (pending → running → completed)
  - Console logs execution progress
  - Dataset Navigation panel auto-expands
  - Results populate in file tree
```

#### 7. View Results
```
User Action: 
  - Select workflow node or dataset
  - Explore file tree
  - Preview output files
System Response:
  - File tree filters to relevant datasets
  - Selected datasets highlighted
  - Preview panel shows file contents
```

---

## State Management Architecture

### App-Level State (App.tsx)

```typescript
// Node and workflow state
selectedNode: any | null          // Currently selected workflow node
selectedAssay: string | null      // Selected assay from study design
isAssembled: boolean             // Workflow assembly status
isWorkflowRunning: boolean       // Workflow execution status

// Upload and document state
uploadedPdfUrl: string           // Persistent PDF URL
hasUploadedFiles: boolean        // Derived from uploadedPdfUrl

// Viewer state
viewerPdfUrl: string             // PDF shown in viewer
isViewerVisible: boolean         // Viewer panel visibility
activePropertyId: string         // Active citation/property
shouldCollapseViewer: boolean    // Viewer collapse flag

// Panel collapse state
isLeftPanelCollapsed: boolean    // Upload & Study Design panel
isWorkflowCollapsed: boolean     // Workflow assembler (unused)
isDatasetNavCollapsed: boolean   // Results panel
isConsoleCollapsed: boolean      // Console panel

// UI interaction state
consoleHeight: number            // Console panel height
isResizingConsole: boolean       // Console resize active
collapseAllExceptSelected: boolean // Workflow focus mode
defaultViewerPlugin: string      // PDF viewer plugin choice
selectedDatasetId: string | null // Selected dataset for highlighting
```

### State Persistence Rules

1. **Survives Panel Collapse**: `uploadedPdfUrl`, derived states
2. **Reset on Panel Collapse**: Component-local states (files array)
3. **Derived States**: `hasUploadedFiles = !!uploadedPdfUrl`

### Critical State Dependencies

```
uploadedPdfUrl → hasUploadedFiles → {
  UploadModule.isExpanded (start collapsed if true)
  StudyDesignModule.isExpanded (start expanded if true)
  StudyDesignModule content visibility
}

selectedAssay → {
  WorkflowAssemblerModule workflow generation
  Assemble Workflow button enabled
}

selectedNode → {
  DatasetNavigationModule filtering
  Node highlighting in workflow canvas
}

selectedDatasetId → {
  Dataset highlighting in measurement nodes
  File tree highlighting in Dataset Navigation
}
```

---

## Component Communication Patterns

### Callback Flow

```
UploadModule
  └─> onPdfUpload(url) → App.uploadedPdfUrl

StudyDesignModule
  └─> onSelectAssay(id) → App.selectedAssay
  └─> onSourceClick(propertyId) → App {viewerPdfUrl, isViewerVisible, activePropertyId}
  └─> onAssembleClick() → App {isAssembled, isLeftPanelCollapsed}

WorkflowAssemblerModule
  └─> onSelectNode(node) → App.selectedNode
  └─> onDatasetSelect(id) → App.selectedDatasetId
  └─> onRunWorkflow() → App {isWorkflowRunning, isDatasetNavCollapsed}
  └─> onCatalogueSourceClick(propertyId) → App viewer state
```

### Props Flow (Top-Down)

```
App
├─> UploadModule {hasUploadedFiles, onPdfUpload, onCollapseLeftPanel}
├─> StudyDesignModule {hasUploadedFiles, selectedAssay, onSelectAssay, onSourceClick, onAssembleClick}
├─> WorkflowAssemblerModule {
│     selectedAssay, selectedNode, isAssembled, hasUploadedFiles,
│     isWorkflowRunning, viewerPdfUrl, isViewerVisible, activePropertyId,
│     shouldCollapseViewer, defaultViewerPlugin, selectedDatasetId,
│     onSelectNode, onDatasetSelect, onRunWorkflow
│   }
└─> DatasetNavigationModule {selectedNode, defaultViewerPlugin, selectedDatasetId}
```

---

## Visual Design Specifications

### Color System
```css
/* Primary Colors */
Blue (Primary):    #2563eb
Purple (Tools):    #9333ea
Green (Models):    #16a34a
Red (Errors):      #dc2626

/* Neutral Palette */
Slate 50:  #f8fafc (backgrounds)
Slate 100: #f1f5f9 (hover states)
Slate 200: #e2e8f0 (borders)
Slate 300: #cbd5e1 (dividers)
Slate 400: #94a3b8 (muted text)
Slate 500: #64748b (secondary text)
Slate 600: #475569 (icons)
Slate 700: #334155 (primary text)
Slate 900: #0f172a (headings)
```

### Typography
```css
/* Uses system defaults from Tailwind v4 */
Headings (h1): Larger, bold
Body text: Default size
Small text: .text-xs (11-12px)
Labels: .text-sm (13-14px)
```

### Spacing
```css
Module padding: 16px (p-4)
Section gaps: 8px (gap-2)
Icon spacing: 8px (gap-2)
Border radius: 8px (rounded-lg)
```

### Interactive States
```css
Hover: bg-slate-50, border-blue-400
Focus: ring-2 ring-blue-500
Selected: border-blue-500, shadow-lg
Active: bg-blue-50
```

### Status Indicators
```css
Completed: green border, green icon
Running: blue border, spinning icon
Pending: gray border, gray icon
Error: red border, red icon
```

---

## Panel Resize Specifications

### Horizontal Panels (Left/Right)

**Left Panel (Upload & Study Design)**:
- Default width: 320px
- Min width: 280px
- Max width: 600px
- Resize handle: Right border

**Right Panel (Results)**:
- Default width: 320px
- Min width: 280px
- Max width: 600px
- Resize handle: Left border

**Resize Behavior**:
- Smooth drag interaction
- Visual feedback on hover
- Constrains to min/max bounds
- Persists during session

### Vertical Panel (Console)

**Console**:
- Default height: 200px
- Min height: 100px
- Max height: window.innerHeight - 200px
- Resize handle: Top border (1px hover target)

**Resize Behavior**:
- Drag top border to resize
- Cursor changes to ns-resize
- Hover highlights border (blue)
- Smooth height updates

---

## Example: Breast Cancer Segmentation Workflow

### Dataset: MAMA-MIA
Multi-center breast cancer imaging dataset with DCE-MRI scans and tumor segmentations.

### Workflow Steps

1. **Upload Publication**
   - PDF: "Deep Learning for Breast Cancer Segmentation in DCE-MRI"

2. **Study Design Extraction**
   ```
   Study: Breast Cancer Segmentation
   ├── Subjects: 1506 patients
   ├── Samples: DCE-MRI scans
   └── Assays
       └── Tumor Segmentation
           ├── Inputs: DCE-MRI Scans
           ├── Samples: 3D volumes (T1w.nii.gz)
           └── Outputs: Tumor Segmentation masks
   ```

3. **Assembled Workflow**
   ```
   [Input: DCE-MRI Scans] → [Tool: Preprocessing] → [Tool: U-Net Segmentation] → [Output: Tumor Segmentation]
   ```

4. **Dataset Structure**
   ```
   MAMA-MIA/
   ├── primary/DCE-MRI/
   │   ├── Subject_001/T1w.nii.gz
   │   ├── Subject_002/T1w.nii.gz
   │   └── Subject_003/T1w.nii.gz
   └── derivative/segmentation/
       ├── Subject_001/tumor_mask.nii.gz
       └── Subject_002/tumor_mask.nii.gz
   ```

5. **Execution**
   - Run workflow → Process all subjects
   - Real-time status updates
   - Results saved to derivative folder

---

## Technical Implementation Details

### Key Libraries

```json
{
  "react": "^18.x",
  "react-dnd": "^16.0.1",
  "react-dnd-html5-backend": "^16.0.1",
  "lucide-react": "latest",
  "tailwindcss": "^4.0"
}
```

### File Structure

```
/
├── App.tsx                          # Main application container
├── components/
│   ├── UploadModule.tsx             # File upload interface
│   ├── StudyDesignModule.tsx        # Study tree viewer
│   ├── WorkflowAssemblerModule.tsx  # Main workflow area
│   │   ├── WorkflowCanvas.tsx       # Graph editor
│   │   ├── DataObjectCatalogue.tsx  # Data browser
│   │   └── ViewerPanel.tsx          # PDF viewer
│   ├── DatasetNavigationModule.tsx  # Results file tree
│   ├── ConsoleModule.tsx            # Log viewer
│   ├── ConfigurationPanel.tsx       # Settings menu
│   ├── GraphNode.tsx                # Workflow node component
│   ├── ResizablePanel.tsx           # Horizontal resize wrapper
│   ├── CollapsibleHorizontalPanel.tsx # Collapsible wrapper
│   └── figma/
│       └── ImageWithFallback.tsx    # Protected image component
└── styles/
    └── globals.css                   # Tailwind v4 config
```

### Protected Files
- `/components/figma/ImageWithFallback.tsx` - Do not modify

---

## Edge Cases and Error Handling

### Panel State Management
- **Issue**: Component state resets on unmount
- **Solution**: Lift critical state to App.tsx
- **Example**: `hasUploadedFiles` derived from persisted `uploadedPdfUrl`

### Nested Buttons
- **Issue**: Button inside button warning
- **Solution**: Siblings in flex container instead of nesting

### Form Inputs Without Handlers
- **Issue**: Select with value but no onChange
- **Solution**: Add `readOnly` attribute for display-only selects

### Viewer Toggle
- **Issue**: Clicking source button when viewer already open
- **Solution**: Force re-render with visibility toggle setTimeout

---

## Future Enhancements

### Phase 2 Features
1. **Real Backend Integration**
   - Apache Airflow connection
   - Actual workflow execution
   - Result streaming

2. **Enhanced Viewer**
   - Multi-format support (images, videos, 3D)
   - Annotation tools
   - Side-by-side comparison

3. **Export Capabilities**
   - CWL file export
   - Dataset packaging
   - Report generation

4. **Collaboration**
   - Multi-user workflows
   - Comments and reviews
   - Version control

### Phase 3 Features
1. **Advanced AI Agents**
   - Improved extraction accuracy
   - Multi-paper synthesis
   - Automatic error detection

2. **Workflow Marketplace**
   - Share workflows
   - Template library
   - Community contributions

3. **Cloud Execution**
   - Distributed computing
   - Resource optimization
   - Cost management

---

## Reproduction Instructions

### To Recreate This Interface

1. **Initialize Project**
   ```bash
   npm create vite@latest veriflow -- --template react-ts
   cd veriflow
   npm install
   ```

2. **Install Dependencies**
   ```bash
   npm install react-dnd@16.0.1 react-dnd-html5-backend@16.0.1 lucide-react
   npm install -D tailwindcss@4.0
   ```

3. **Setup Tailwind v4**
   - Create `/styles/globals.css` with Tailwind imports
   - Configure default styles for headings, buttons, etc.

4. **Create Component Structure**
   - Follow file structure above
   - Implement components in order: ResizablePanel → UploadModule → StudyDesignModule → WorkflowAssemblerModule → DatasetNavigationModule → ConsoleModule

5. **Implement State Management**
   - Start with App.tsx state structure
   - Add callbacks for child-to-parent communication
   - Pass props down to children

6. **Add Interactivity**
   - Drag-and-drop with react-dnd
   - Panel resize handlers
   - Collapse/expand logic

7. **Style with Tailwind**
   - Apply color system
   - Add hover/focus states
   - Ensure responsive behavior

8. **Test User Flows**
   - Upload → Study Design → Assemble → Run → Results
   - Panel collapse/expand persistence
   - State management edge cases

---

## Key Design Decisions

### Why Derived State?
**Decision**: `hasUploadedFiles = !!uploadedPdfUrl`  
**Reason**: Single source of truth, prevents state desync  
**Benefit**: Persists across component unmount/remount

### Why Separate Viewer State?
**Decision**: Viewer state in App.tsx, not in StudyDesignModule  
**Reason**: Viewer used by multiple modules (Study Design, Catalogue)  
**Benefit**: Centralized control, easier to manage

### Why Auto-Collapse After Upload?
**Decision**: Upload module collapses, Study Design expands  
**Reason**: Progressive disclosure, guides user to next step  
**Benefit**: Clear workflow progression

### Why Measurement Nodes Use Collections?
**Decision**: Nodes contain multiple datasets with consistent naming  
**Reason**: Aligns with SPARC/ISA standards, supports multi-sample workflows  
**Benefit**: Scalable to complex research workflows

### Why Collapsible Left Panel on Assembly?
**Decision**: Auto-collapse left panel when assembling workflow  
**Reason**: Maximize canvas space for workflow editing  
**Benefit**: Better UX for complex workflow assembly

---

## Glossary

**Assay**: A specific experimental procedure or measurement technique  
**CWL**: Common Workflow Language - standard for describing workflows  
**Dataset**: Collection of related data files (e.g., all MRI scans)  
**ISA Framework**: Investigation-Study-Assay metadata standard  
**Measurement Node**: Workflow node representing data collection  
**SDS**: SPARC Dataset Structure - standardized folder organization  
**Sample**: Individual data item within a dataset (e.g., single subject scan)  
**Tool Node**: Workflow node representing a processing step  
**Workflow**: Directed graph of data processing steps

---

## Support and Contribution

### Bug Reports
When reporting issues, include:
- Steps to reproduce
- Expected vs actual behavior
- Browser/environment details
- Console errors
- State of panels/modules

### Feature Requests
Describe:
- Use case
- Expected behavior
- How it fits workflow progression
- Impact on existing functionality

---

**Version**: 1.0  
**Last Updated**: January 2026  
**Author**: VeriFlow Development Team