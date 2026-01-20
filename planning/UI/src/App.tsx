import { useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { UploadModule } from './components/UploadModule';
import { StudyDesignModule } from './components/StudyDesignModule';
import { WorkflowAssemblerModule } from './components/WorkflowAssemblerModule';
import { ConsoleModule } from './components/ConsoleModule';
import { DatasetNavigationModule } from './components/DatasetNavigationModule';
import { ConfigurationPanel } from './components/ConfigurationPanel';

export default function App() {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedAssay, setSelectedAssay] = useState<string | null>(null);

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen w-screen flex flex-col bg-slate-50">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <h1 className="font-semibold text-slate-900">VeriFlow</h1>
              <p className="text-xs text-slate-500">The Verifiable Workflow Architect</p>
            </div>
          </div>
          <ConfigurationPanel />
        </header>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Sidebar - Upload & Study Design */}
          <div className="w-80 border-r border-slate-200 bg-white flex flex-col overflow-hidden">
            <UploadModule />
            <StudyDesignModule 
              onSelectAssay={setSelectedAssay}
              selectedAssay={selectedAssay}
            />
          </div>

          {/* Center Area - Workflow & Console */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <WorkflowAssemblerModule 
              selectedAssay={selectedAssay}
              onSelectNode={setSelectedNode}
              selectedNode={selectedNode}
            />
            <ConsoleModule />
          </div>

          {/* Right Sidebar - Dataset Navigation */}
          <div className="w-96 border-l border-slate-200 bg-white flex flex-col overflow-hidden">
            <DatasetNavigationModule />
          </div>
        </div>
      </div>
    </DndProvider>
  );
}