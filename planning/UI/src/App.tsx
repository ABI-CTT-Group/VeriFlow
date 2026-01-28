import { useState, useEffect } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { UploadModule } from './components/UploadModule';
import { StudyDesignModule } from './components/StudyDesignModule';
import { WorkflowAssemblerModule } from './components/WorkflowAssemblerModule';
import { ConsoleModule } from './components/ConsoleModule';
import { DatasetNavigationModule } from './components/DatasetNavigationModule';
import { ConfigurationPanel } from './components/ConfigurationPanel';
import { CollapsibleHorizontalPanel } from './components/CollapsibleHorizontalPanel';
import { ResizablePanel } from './components/ResizablePanel';
import { ViewerPanel } from './components/ViewerPanel';
import { DataObjectCatalogue } from './components/DataObjectCatalogue';
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp } from 'lucide-react';

export default function App() {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedAssay, setSelectedAssay] = useState<string | null>(null);
  const [uploadedPdfUrl, setUploadedPdfUrl] = useState<string>('');
  // Derive hasUploadedFiles from uploadedPdfUrl instead of separate state
  const hasUploadedFiles = !!uploadedPdfUrl;
  const [viewerPdfUrl, setViewerPdfUrl] = useState<string>('');
  const [isViewerVisible, setIsViewerVisible] = useState(false);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);
  const [isWorkflowCollapsed, setIsWorkflowCollapsed] = useState(false);
  const [isDatasetNavCollapsed, setIsDatasetNavCollapsed] = useState(true);
  const [isConsoleCollapsed, setIsConsoleCollapsed] = useState(false);
  const [consoleHeight, setConsoleHeight] = useState(200);
  const [activePropertyId, setActivePropertyId] = useState<string>('');
  const [isAssembled, setIsAssembled] = useState(false);
  const [shouldCollapseViewer, setShouldCollapseViewer] = useState(false);
  const [isResizingConsole, setIsResizingConsole] = useState(false);
  const [isWorkflowRunning, setIsWorkflowRunning] = useState(false);
  const [collapseAllExceptSelected, setCollapseAllExceptSelected] = useState(false);
  const [defaultViewerPlugin, setDefaultViewerPlugin] = useState<string>('auto');
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);

  const handleSourceClick = (propertyId: string) => {
    setViewerPdfUrl(uploadedPdfUrl);
    // Toggle isViewerVisible to force re-expansion even if already visible
    setIsViewerVisible(false);
    setTimeout(() => {
      setIsViewerVisible(true);
    }, 0);
    setActivePropertyId(propertyId);
    setShouldCollapseViewer(false); // Expand viewer when source is clicked
    // Expand workflow assembler if collapsed
    if (isWorkflowCollapsed) {
      setIsWorkflowCollapsed(false);
    }
  };

  const handleViewerClose = () => {
    setIsViewerVisible(false);
    setActivePropertyId('');
  };

  const handlePdfUpload = (pdfUrl: string) => {
    setUploadedPdfUrl(pdfUrl);
  };

  const handleAssembleClick = () => {
    setIsAssembled(true);
    // Close the viewer when assembling
    setIsViewerVisible(false);
    setActivePropertyId('');
    setShouldCollapseViewer(true); // Collapse the viewer panel
    // Ensure workflow assembler is visible
    if (isWorkflowCollapsed) {
      setIsWorkflowCollapsed(false);
    }
    // Collapse the left panel to give more space to workflow assembler
    setIsLeftPanelCollapsed(true);
  };

  const handleRunWorkflow = () => {
    setIsWorkflowRunning(true);
    setCollapseAllExceptSelected(true);
    setIsDatasetNavCollapsed(false); // Auto-expand results panel
  };

  const handleConsoleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingConsole(true);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isResizingConsole) {
      const newHeight = window.innerHeight - e.clientY;
      const minHeight = 100;
      const maxHeight = window.innerHeight - 200;
      setConsoleHeight(Math.min(Math.max(newHeight, minHeight), maxHeight));
    }
  };

  const handleMouseUp = () => {
    setIsResizingConsole(false);
  };

  // Add event listeners for console resize
  useEffect(() => {
    if (isResizingConsole) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isResizingConsole]);

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen flex flex-col bg-slate-50 overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
              <span className="text-white font-bold text-sm">VF</span>
            </div>
            <div>
              <h1 className="font-semibold text-slate-900">VeriFlow</h1>
              <p className="text-xs text-slate-500">Research Reproducibility Engineer</p>
            </div>
          </div>
          <ConfigurationPanel 
            defaultViewerPlugin={defaultViewerPlugin}
            onViewerPluginChange={setDefaultViewerPlugin}
          />
        </header>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          {/* Left Panel - Upload & Review Study Design */}
          {!isLeftPanelCollapsed && (
            <ResizablePanel
              side="left"
              defaultWidth={320}
              minWidth={280}
              maxWidth={600}
            >
              <div className="h-full flex flex-col bg-white border-r border-slate-200 overflow-hidden">
                <UploadModule 
                  onPdfUpload={handlePdfUpload}
                  onCollapseLeftPanel={() => setIsLeftPanelCollapsed(true)}
                  hasUploadedFiles={hasUploadedFiles}
                />
                <StudyDesignModule 
                  onSelectAssay={setSelectedAssay}
                  selectedAssay={selectedAssay}
                  hasUploadedFiles={hasUploadedFiles}
                  onSourceClick={handleSourceClick}
                  onAssembleClick={handleAssembleClick}
                  onCollapseLeftPanel={() => setIsLeftPanelCollapsed(true)}
                />
              </div>
            </ResizablePanel>
          )}

          {/* Collapsed left panel */}
          {isLeftPanelCollapsed && (
            <div className="w-8 bg-slate-50 border-r border-slate-200 flex-shrink-0">
              <button
                onClick={() => setIsLeftPanelCollapsed(false)}
                className="h-full w-full hover:bg-slate-100 transition-colors flex items-center justify-center"
              >
                <span className="text-xs font-medium text-slate-600 whitespace-nowrap" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
                  Upload & Review Study Design
                </span>
              </button>
            </div>
          )}

          {/* Middle Panel - Workflow Assembler */}
          <div className="flex-1 flex flex-col bg-white overflow-hidden min-w-0">
            <WorkflowAssemblerModule 
              selectedAssay={selectedAssay}
              onSelectNode={setSelectedNode}
              selectedNode={selectedNode}
              viewerPdfUrl={viewerPdfUrl}
              isViewerVisible={isViewerVisible}
              onViewerClose={handleViewerClose}
              activePropertyId={activePropertyId}
              isAssembled={isAssembled}
              shouldCollapseViewer={shouldCollapseViewer}
              onCatalogueSourceClick={handleSourceClick}
              hasUploadedFiles={hasUploadedFiles}
              isWorkflowRunning={isWorkflowRunning}
              setCollapseAllExceptSelected={setCollapseAllExceptSelected}
              defaultViewerPlugin={defaultViewerPlugin}
              onRunWorkflow={handleRunWorkflow}
              onDatasetSelect={setSelectedDatasetId}
              selectedDatasetId={selectedDatasetId}
            />
          </div>

          {/* Right Panel - Visualise and Export Results */}
          <CollapsibleHorizontalPanel
            isCollapsed={isDatasetNavCollapsed}
            onToggle={() => setIsDatasetNavCollapsed(!isDatasetNavCollapsed)}
            side="right"
            defaultWidth={320}
            label="Visualise and Export Results"
          >
            <div className="h-full flex flex-col bg-white border-l border-slate-200 overflow-hidden">
              {/* Header with inline chevron */}
              <div className="px-4 py-3 border-b border-slate-200 flex-shrink-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700">4. Visualise and Export Results</span>
                  <button
                    onClick={() => setIsDatasetNavCollapsed(true)}
                    className="text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">Select a Workflow Item to View it's Results</p>
              </div>

              {/* Content */}
              <div className={`flex-1 flex flex-col overflow-hidden ${isDatasetNavCollapsed ? 'hidden' : 'flex'}`}>
                <DatasetNavigationModule 
                  selectedNode={selectedNode}
                  defaultViewerPlugin={defaultViewerPlugin}
                  selectedDatasetId={selectedDatasetId}
                />
              </div>
            </div>
          </CollapsibleHorizontalPanel>
        </div>

        {/* Bottom Panel - Console */}
        {!isConsoleCollapsed ? (
          <div className="border-t border-slate-200 flex-shrink-0 bg-white relative" style={{ height: `${consoleHeight}px` }}>
            {/* Resize handle */}
            <div
              onMouseDown={handleConsoleMouseDown}
              className="absolute top-0 left-0 right-0 h-1 cursor-ns-resize hover:bg-blue-500 transition-colors z-20"
            />
            <div className="h-full flex flex-col overflow-hidden" style={{ paddingTop: '4px' }}>
              {/* Header with collapse button */}
              <div className="px-4 py-2 flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsConsoleCollapsed(true)}
                    className="text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                  <span className="text-sm font-medium text-slate-700">Console</span>
                </div>
              </div>
              {/* Content */}
              <div className="flex-1 overflow-hidden">
                <ConsoleModule />
              </div>
            </div>
          </div>
        ) : (
          <div className="border-t border-slate-200 flex-shrink-0 bg-slate-50" style={{ height: '32px' }}>
            <button
              onClick={() => setIsConsoleCollapsed(false)}
              className="w-full h-full hover:bg-slate-100 transition-colors flex items-center justify-center gap-2"
            >
              <ChevronUp className="w-4 h-4 text-slate-600" />
              <span className="text-xs font-medium text-slate-600">Console</span>
            </button>
          </div>
        )}
      </div>
    </DndProvider>
  );
}