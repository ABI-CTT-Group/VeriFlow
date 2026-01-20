import { useState } from 'react';

interface ConnectionLineProps {
  id: string;
  sourceNode: any;
  targetNode: any;
  sourcePortIndex: number;
  targetPortIndex: number;
  onDelete: (id: string) => void;
}

export function ConnectionLine({ 
  id, 
  sourceNode, 
  targetNode, 
  sourcePortIndex, 
  targetPortIndex,
  onDelete 
}: ConnectionLineProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Calculate port positions
  const startX = sourceNode.x + 280; // node width
  const startY = sourceNode.y + 70 + sourcePortIndex * 28; // header height + port spacing
  const endX = targetNode.x;
  const endY = targetNode.y + 70 + targetPortIndex * 28;

  // Calculate control points for bezier curve
  const controlPoint1X = startX + (endX - startX) * 0.5;
  const controlPoint2X = startX + (endX - startX) * 0.5;

  const pathD = `M ${startX} ${startY} C ${controlPoint1X} ${startY}, ${controlPoint2X} ${endY}, ${endX} ${endY}`;

  // Calculate midpoint for delete button
  const midX = (startX + endX) / 2;
  const midY = (startY + endY) / 2;

  return (
    <g>
      {/* Invisible thicker line for easier hovering */}
      <path
        d={pathD}
        stroke="transparent"
        strokeWidth="12"
        fill="none"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{ cursor: 'pointer', pointerEvents: 'stroke' }}
      />
      
      {/* Visible line */}
      <path
        d={pathD}
        stroke={isHovered ? '#3b82f6' : '#64748b'}
        strokeWidth="2"
        fill="none"
        style={{ pointerEvents: 'none' }}
      />

      {/* Delete button on hover */}
      {isHovered && (
        <g>
          <circle
            cx={midX}
            cy={midY}
            r="10"
            fill="#ef4444"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(id);
            }}
            style={{ cursor: 'pointer', pointerEvents: 'auto' }}
          />
          <line
            x1={midX - 4}
            y1={midY - 4}
            x2={midX + 4}
            y2={midY + 4}
            stroke="white"
            strokeWidth="2"
            style={{ pointerEvents: 'none' }}
          />
          <line
            x1={midX + 4}
            y1={midY - 4}
            x2={midX - 4}
            y2={midY + 4}
            stroke="white"
            strokeWidth="2"
            style={{ pointerEvents: 'none' }}
          />
        </g>
      )}
    </g>
  );
}
