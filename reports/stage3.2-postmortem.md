# Stage 3.2 Postmortem: UI Parity Failure Analysis

## Incident Summary
During Stage 3.2 (UI Visual Refinement), significant delays occurred in achieving visual parity between the Vue 3 port and the React reference. The initial port resulted in a "flat", "ugly" UI that lacked the premium feel of the reference, despite component-level code appearing identical.

## Root Cause Analysis

### 1. The Incorrect Assumption
The development process operated under the false assumption that **Component Code (.tsx/.vue)** was the primary source of truth for styling. We assumed that because both projects used Tailwind CSS (`className` vs `class`), copying the utility classes would result in an identical UI.

### 2. The Missing Link: Global CSS
We failed to recognize that the React reference relied on a comprehensive **1760-line `index.css`** file. This file defined:
*   **Design Tokens**: Custom Shadcn/UI variables (`--primary`, `--muted`, `--accent`).
*   **Color Scale**: Specific Oklch color definitions that overrode default Tailwind colors (e.g., `bg-slate-50`).
*   **Typography**: Base font settings (`Inter`) and line-height scales.
*   **Resets**: Custom CSS resets and base layer behaviors.

By missing this file, the Vue app used default Tailwind values, resulting in:
*   Different color shades (Hex vs Oklch).
*   Default system fonts instead of Inter.
*   Missing component styling variables.

### 3. Verification Blind Spots
*   **Tool Failure**: The browser verification tool failed, preventing visual diffing.
*   **Code-Only Review**: We defended the implementation based on "matching classes" in the component files, ignoring the fact that those classes mapped to different underlying CSS values due to the missing global context.

## Resolution
The issue was resolved by **synchronizing the Global CSS**:
1.  The entire content of React's `index.css` was copied to Vue's `style.css`.
2.  This instantly aligned the foundational design system (colors, fonts, spacing).
3.  Component-specific "premium" enhancements (shadows, rounded corners) were then applied as a deliberate layer on top.

## Lessons Learned & Protocol Updates

### New "Source of Truth" Hierarchy
Per the updated `PLAN.md`, all future UI work must strictly follow this priority:
1.  **Global CSS / Design System** (`index.css`, theme tokens)
2.  **Screenshot Reference** (`UI.jpg`)
3.  **Component Structure**
4.  **Markup Code**

### Action Items
*   **Always check `index.css`/`globals.css` first** when porting a new project.
*   **Never assume Tailwind defaults match** an existing project's design system.
*   **Visual parity requires Design System parity**, not just Class parity.
