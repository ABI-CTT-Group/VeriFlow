import { ReactNode, useRef, useState, useEffect } from 'react';

interface ResizablePanelProps {
  children: ReactNode;
  side: 'left' | 'right';
  minWidth?: number;
  maxWidth?: number;
  defaultWidth?: number;
  className?: string;
}

export function ResizablePanel({
  children,
  side = 'left',
  minWidth = 250,
  maxWidth = 600,
  defaultWidth = 320,
  className = ''
}: ResizablePanelProps) {
  const [width, setWidth] = useState(defaultWidth);
  const [isResizing, setIsResizing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const panel = panelRef.current;
      if (!panel) return;

      const rect = panel.getBoundingClientRect();
      let newWidth: number;

      if (side === 'left') {
        newWidth = e.clientX - rect.left;
      } else {
        newWidth = rect.right - e.clientX;
      }

      // Constrain width
      newWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, side, minWidth, maxWidth]);

  return (
    <div
      ref={panelRef}
      className={`relative bg-white border-slate-200 flex-shrink-0 ${
        side === 'left' ? 'border-r' : 'border-l'
      } ${className}`}
      style={{ width: `${width}px` }}
    >
      {/* Content */}
      {children}

      {/* Resize Handle */}
      <div
        className={`absolute top-0 bottom-0 w-1 hover:w-1.5 bg-transparent hover:bg-blue-400 cursor-col-resize transition-all ${
          side === 'left' ? 'right-0' : 'left-0'
        } ${isResizing ? 'bg-blue-500 w-1.5' : ''}`}
        onMouseDown={() => setIsResizing(true)}
      />
    </div>
  );
}
