import { useState, ReactNode } from 'react';
import { Resizable } from 're-resizable';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface ResizablePanelProps {
  title: string;
  children: ReactNode;
  defaultHeight?: number;
  defaultCollapsed?: boolean;
}

export function ResizablePanel({ 
  title, 
  children, 
  defaultHeight = 300,
  defaultCollapsed = false 
}: ResizablePanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  return (
    <Resizable
      defaultSize={{ width: '100%', height: isCollapsed ? 40 : defaultHeight }}
      enable={{ 
        top: false, 
        right: false, 
        bottom: !isCollapsed, 
        left: false 
      }}
      minHeight={isCollapsed ? 40 : 100}
      className="border-b border-slate-200"
    >
      <div className="h-full flex flex-col bg-white">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center justify-between px-4 py-2 border-b border-slate-200 hover:bg-slate-50 transition-colors"
        >
          <span className="text-sm font-medium text-slate-700">{title}</span>
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </button>
        {!isCollapsed && (
          <div className="flex-1 overflow-auto">
            {children}
          </div>
        )}
      </div>
    </Resizable>
  );
}
