import { ChevronLeft, ChevronRight } from 'lucide-react';
import { ReactNode } from 'react';

interface CollapsibleHorizontalPanelProps {
  children: ReactNode;
  isCollapsed: boolean;
  onToggle: () => void;
  side: 'left' | 'right' | 'middle';
  defaultWidth?: number;
  className?: string;
  label?: string;
}

export function CollapsibleHorizontalPanel({ 
  children, 
  isCollapsed,
  onToggle,
  defaultWidth = 320,
  side = 'left',
  className = '',
  label = 'Panel'
}: CollapsibleHorizontalPanelProps) {
  return (
    <div 
      className={`relative bg-white border-slate-200 transition-all duration-300 ${
        side === 'left' ? 'border-r' : side === 'right' ? 'border-l' : ''
      } ${className}`}
      style={{ 
        width: isCollapsed ? '32px' : `${defaultWidth}px`,
        flexShrink: 0
      }}
    >
      {/* Collapsed state - show rotated label */}
      {isCollapsed ? (
        <button
          onClick={onToggle}
          className={`h-full w-full bg-slate-50 hover:bg-slate-100 transition-colors flex items-center justify-center ${
            side === 'left' ? 'border-r' : 'border-l'
          } border-slate-200`}
        >
          <span className="text-xs font-medium text-slate-600 whitespace-nowrap" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
            {label}
          </span>
        </button>
      ) : null}

      {/* Content */}
      <div className={`h-full ${isCollapsed ? 'hidden' : 'block'}`}>
        {children}
      </div>
    </div>
  );
}