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

## 5. Black Box Visual Artifact on Workflow Nodes

### Issue
After refactoring the workflow panel to use the `Vue Flow` library, nodes appeared with a black/transparent background box behind or around them, disrupting the visual design. This was caused by default styles from the `Vue Flow` library conflicting with the custom node implementation.

### Solution
**File:** `frontend/src/style.css`
**Change:** added global CSS overrides to force `transparent` backgrounds and remove borders/shadows from Vue Flow's internal node wrappers, ensuring only the custom `GraphNode` component's style is visible.

```css
/* frontend/src/style.css */
.vue-flow__node {
  background: transparent !important;
  border: none !important;
  width: auto !important;
  box-shadow: none !important;
}

.vue-flow__node-default,
.vue-flow__node-input,
.vue-flow__node-output,
.vue-flow__node-group {
    background: transparent !important;
    border: none !important;
}
```

## 6. Upload Publication Panel Not Closing Automatically

### Issue
The "Upload Publication" panel remained open even after a file was successfully uploaded or a demo was loaded, requiring the user to manually close it to proceed to the "Review Study Design" step.

### Solution
**File:** `frontend/src/components/modules/UploadModule.vue`
**Change:** Added a `watch` effect on the `hasUploadedFiles` prop. When this prop becomes true (indicating files are present), the local component state `isExpanded` is automatically set to `false`.

```typescript
// frontend/src/components/modules/UploadModule.vue
watch(() => props.hasUploadedFiles, (hasFiles) => {
  if (hasFiles) {
    isExpanded.value = false
  }
})
```

## 7. Assay Properties Panel Not Resizable

### Issue
The "Review Study Design" panel had a fixed layout (50/50 split) between the Tree View (ISA Hierarchy) and the Property Editor. Users could not adjust the height of the tree view to see more items, which was restrictive for large study designs.

### Solution
**File:** `frontend/src/components/modules/StudyDesignModule.vue`
**Change:** Wrapped the Tree View section in a `<ResizablePanel>` component with vertical orientation. This allows users to drag the horizontal divider between the tree view and the property editor to adjust their relative heights.

```vue
<!-- frontend/src/components/modules/StudyDesignModule.vue -->
<template>
  <ResizablePanel
    orientation="vertical"
    :default-height="300"
    :min-height="150"
    :max-height="600"
  >
    <div class="px-3 py-3 space-y-1 overflow-auto h-full">
      <!-- Tree View Content -->
    </div>
  </ResizablePanel>
</template>
```
