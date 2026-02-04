# VeriFlow UI Bug Report & Solutions

**Date:** 2026-02-03
**Status:** Fixed

## 1. "Visualise and Export Results" Panel Default State

### Issue
The right-hand panel ("4. Visualise and Export Results") was open by default on application load, occupying screen space unnecessarily before any results were generated.

### Solution
**File:** `frontend/src/stores/workflow.ts`
**Change:** Updated the default value of `isRightPanelCollapsed` from `false` to `true`.

```typescript
// stores/workflow.ts
const isRightPanelCollapsed = ref(true) // Changed from false
```

## 2. "Review Study Design" Panel Scrolling Issue

### Issue
In the "2. Review Study Design" panel, the left-side "Tree View" (ISA Hierarchy) expanded indefinitely as items were opened. Because the parent container had `overflow: hidden` and the tree container had `flex-shrink-0`, the property editor panel was pushed off-screen, and the tree view itself was not scrollable.

### Solution
**File:** `frontend/src/components/modules/StudyDesignModule.vue`
**Change:** Removed `flex-shrink-0` and applied `flex-1 min-h-0` to the Tree View container. This forces the Tree View and Property Editor to share the available vertical space within the parent flex column, enabling independent scrolling for both.

```vue
<!-- components/modules/StudyDesignModule.vue -->
<div class="px-3 py-3 space-y-1 border-b border-slate-200 overflow-auto flex-1 min-h-0">
  <!-- Content -->
</div>
```

## 3. Visible Scrollbars

### Issue
Standard browser scrollbars were visible, detracting from the desired "premium/clean" aesthetic of the application.

### Solution
**File:** `frontend/src/style.css`
**Change:** Added global CSS rules to hide scrollbars across all major browsers while retaining scrolling functionality via mouse wheel/trackpad.

```css
/* frontend/src/style.css */

/* Hide scrollbar for Chrome, Safari and Opera */
::-webkit-scrollbar {
  display: none;
}

/* Hide scrollbar for IE, Edge and Firefox */
* {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

## 4. Workflow Connection Alignment, Deletion, and Routing

### Issue
1.  **Alignment**: Connection lines were anchoring to arbitrary offsets rather than the visualization ports on the nodes, causing them to float disconnectedly.
2.  **Deletion**: Users could not delete connections because connection lines were not capturing pointer events.
3.  **Routing/Crossing**: Connection lines would cross or loop unsightly when nodes were placed close together horizontally.

### Solution
**Files**: 
- `frontend/src/components/workflow/GraphNode.vue`
- `frontend/src/components/workflow/ConnectionLine.vue`
- `frontend/src/components/workflow/WorkflowAssemblerModule.vue`

**Changes**:
1.  **Alignment**: Implemented DOM-based positioning. Added unique IDs to node ports and updated the parent component to calculate start/end coordinates based on the actual DOM element positions.
2.  **Deletion**: Added `pointer-events-auto` to the `ConnectionLine` SVG group to ensure click events are captured.
3.  **Routing**: Implemented adaptive Bezier control point offsets based on the horizontal distance between nodes.

```typescript
// frontend/src/components/workflow/ConnectionLine.vue
const distX = props.endX - props.startX
// Adaptive offset prevents huge loops when nodes are close
const controlPointOffset = Math.max(Math.min(distX / 2, 100), 20) 
const pathD = `M ${props.startX} ${props.startY} C ${props.startX + controlPointOffset} ${props.startY}, ...`
```
```
