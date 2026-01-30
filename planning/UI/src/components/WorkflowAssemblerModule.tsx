import { useState, useRef, useCallback, useEffect } from 'react';
import { Play, Square, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { GraphNode } from './GraphNode';
import { ConnectionLine } from './ConnectionLine';
import { ViewerPanel } from './ViewerPanel';
import { DataObjectCatalogue } from './DataObjectCatalogue';
import { ResizablePanel } from './ResizablePanel';

interface WorkflowAssemblerModuleProps {
  selectedAssay: string | null;
  onSelectNode: (node: any) => void;
  selectedNode: any;
  viewerPdfUrl?: string;
  isViewerVisible?: boolean;
  onViewerClose?: () => void;
  activePropertyId?: string;
  isAssembled?: boolean;
  shouldCollapseViewer?: boolean;
  onCatalogueSourceClick?: (propertyId: string) => void;
  hasUploadedFiles?: boolean;
  isWorkflowRunning?: boolean;
  setCollapseAllExceptSelected?: (value: boolean) => void;
  defaultViewerPlugin?: string;
  onRunWorkflow?: () => void;
  onDatasetSelect?: (datasetId: string | null) => void;
  selectedDatasetId?: string;
}

interface Connection {
  id: string;
  sourceNodeId: string;
  sourcePortId: string;
  targetNodeId: string;
  targetPortId: string;
}

interface Port {
  id: string;
  label: string;
  type: 'input' | 'output';
  datasetId?: string;
  sampleId?: string;
}

export function WorkflowAssemblerModule({ 
  selectedAssay, 
  onSelectNode,
  selectedNode,
  viewerPdfUrl,
  isViewerVisible = false,
  onViewerClose,
  activePropertyId,
  isAssembled = false,
  shouldCollapseViewer = false,
  onCatalogueSourceClick,
  hasUploadedFiles,
  isWorkflowRunning,
  setCollapseAllExceptSelected,
  defaultViewerPlugin,
  onRunWorkflow,
  onDatasetSelect,
  selectedDatasetId
}: WorkflowAssemblerModuleProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [numSubjects, setNumSubjects] = useState(1);
  const [connections, setConnections] = useState<Connection[]>([
    { id: 'conn-1', sourceNodeId: 'input-1', sourcePortId: 'out-0', targetNodeId: 'tool-1', targetPortId: 'in-0' },
    { id: 'conn-2', sourceNodeId: 'tool-1', sourcePortId: 'out-0', targetNodeId: 'tool-2', targetPortId: 'in-0' },
    { id: 'conn-3', sourceNodeId: 'model-1', sourcePortId: 'out-0', targetNodeId: 'tool-2', targetPortId: 'in-1' },
    { id: 'conn-4', sourceNodeId: 'tool-2', sourcePortId: 'out-0', targetNodeId: 'tool-3', targetPortId: 'in-0' },
    { id: 'conn-5', sourceNodeId: 'tool-3', sourcePortId: 'out-0', targetNodeId: 'output-1', targetPortId: 'in-0' }
  ]);
  const [dragConnection, setDragConnection] = useState<{ sourceNodeId: string; sourcePortId: string; x: number; y: number } | null>(null);
  const [isViewerCollapsed, setIsViewerCollapsed] = useState(!isViewerVisible || shouldCollapseViewer);
  const [isCatalogueCollapsed, setIsCatalogueCollapsed] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Auto-collapse viewer when shouldCollapseViewer becomes true
  useEffect(() => {
    if (shouldCollapseViewer) {
      setIsViewerCollapsed(true);
    }
  }, [shouldCollapseViewer]);

  // Auto-expand viewer when isViewerVisible becomes true
  useEffect(() => {
    if (isViewerVisible) {
      setIsViewerCollapsed(false);
    }
  }, [isViewerVisible]);

  // Auto-select first input measurement when assay is selected for assembly
  useEffect(() => {
    if (selectedAssay && isAssembled) {
      const firstInputNode = nodes.find(n => n.type === 'measurement' && n.role === 'input');
      if (firstInputNode && !selectedNode) {
        // Select the dataset within the input node, not the node itself
        const firstDataset = firstInputNode.outputs?.[0];
        if (firstDataset?.datasetId && onDatasetSelect) {
          onDatasetSelect(firstDataset.datasetId);
        }
      }
    }
  }, [selectedAssay, isAssembled]);

  const handleRunWorkflow = () => {
    setIsRunning(true);
    if (setCollapseAllExceptSelected) {
      setCollapseAllExceptSelected(true);
    }
    if (onRunWorkflow) {
      onRunWorkflow();
    }
  };

  const handlePortMouseDown = useCallback((nodeId: string, portId: string, portType: 'input' | 'output', event: React.MouseEvent) => {
    if (portType === 'output') {
      event.stopPropagation();
      const rect = canvasRef.current?.getBoundingClientRect();
      if (rect) {
        setDragConnection({
          sourceNodeId: nodeId,
          sourcePortId: portId,
          x: event.clientX - rect.left,
          y: event.clientY - rect.top
        });
      }
    }
  }, []);

  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    if (dragConnection && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      setDragConnection({
        ...dragConnection,
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
      });
    }
  }, [dragConnection]);

  const handlePortMouseUp = useCallback((nodeId: string, portId: string, portType: 'input' | 'output') => {
    if (dragConnection && portType === 'input') {
      // Create new connection
      const newConnection: Connection = {
        id: `conn-${Date.now()}`,
        sourceNodeId: dragConnection.sourceNodeId,
        sourcePortId: dragConnection.sourcePortId,
        targetNodeId: nodeId,
        targetPortId: portId
      };
      setConnections([...connections, newConnection]);
    }
    setDragConnection(null);
  }, [dragConnection, connections]);

  const handleMouseUp = useCallback(() => {
    setDragConnection(null);
  }, []);

  const handleDeleteConnection = useCallback((connectionId: string) => {
    setConnections(connections.filter(c => c.id !== connectionId));
  }, [connections]);

  const getAssayName = () => {
    if (selectedAssay === 'assay-1') return 'U-Net Training Assay';
    if (selectedAssay === 'assay-2') return 'Model Inference Assay';
    return '';
  };

  // Show "Assemble to begin" message if assay is selected but not assembled
  if (selectedAssay && !isAssembled && !isViewerVisible) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 bg-slate-50">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <p className="text-sm font-medium text-slate-600">Ready to assemble</p>
          <p className="text-xs mt-1">Click "Assemble Selected Assay" to generate the workflow</p>
        </div>
      </div>
    );
  }
  
  // Show viewer-only mode when source is clicked but workflow not assembled
  if (selectedAssay && !isAssembled && isViewerVisible) {
    return (
      <div className="h-full flex overflow-hidden bg-white">
        {/* Viewer Panel (Collapsible) */}
        <div 
          className="relative border-r border-slate-200 transition-all duration-300 flex-shrink-0"
          style={{ 
            width: isViewerCollapsed ? '32px' : '400px'
          }}
        >
          {/* Collapsed state - show rotated label */}
          {isViewerCollapsed ? (
            <button
              onClick={() => setIsViewerCollapsed(false)}
              className="h-full w-full bg-slate-50 hover:bg-slate-100 transition-colors flex items-center justify-center border-r border-slate-200"
            >
              <span className="text-xs font-medium text-slate-600 whitespace-nowrap" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
                Document Viewer
              </span>
            </button>
          ) : (
            /* Expanded state - show close button */
            <button
              onClick={() => setIsViewerCollapsed(true)}
              className="absolute top-3 right-3 z-10 w-6 h-6 bg-white border border-slate-200 rounded hover:bg-slate-50 hover:border-slate-300 transition-colors flex items-center justify-center"
            >
              <ChevronLeft className="w-3 h-3 text-slate-600" />
            </button>
          )}

          {/* Content */}
          <div className={`h-full overflow-hidden ${isViewerCollapsed ? 'hidden' : 'block'}`}>
            <ViewerPanel 
              pdfUrl={viewerPdfUrl}
              onClose={onViewerClose}
              activePropertyId={activePropertyId}
            />
          </div>
        </div>

        {/* Empty space showing "Ready to assemble" */}
        <div className="flex-1 flex items-center justify-center text-slate-400 bg-slate-50">
          <div className="text-center">
            <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            <p className="text-sm font-medium text-slate-600">Ready to assemble</p>
            <p className="text-xs mt-1">Click "Assemble Selected Assay" to generate the workflow</p>
          </div>
        </div>
      </div>
    );
  }

  if (!selectedAssay) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 bg-slate-50">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <p className="text-sm">{hasUploadedFiles ? "Select an assay from Study Design to assemble it's workflow" : "Upload a paper to begin"}</p>
        </div>
      </div>
    );
  }

  // Node positions
  const nodes = [
    {
      id: 'input-1',
      type: 'measurement',
      role: 'input',
      name: 'Input Measurements',
      x: 50,
      y: 50,
      outputs: [
        { id: 'out-0', label: 'MRI Scan', datasetId: 'dce-mri-scans', sampleId: 'Subject_001/T1w.nii.gz' }
      ],
      totalSubjects: 384
    },
    {
      id: 'tool-1',
      type: 'tool',
      name: 'DICOM to NIfTI',
      x: 450,
      y: 50,
      status: 'completed',
      confidence: 0.95,
      inputs: [
        { id: 'in-0', label: 'Raw DICOM' }
      ],
      outputs: [
        { id: 'out-0', label: 'NIfTI Volume' }
      ]
    },
    {
      id: 'tool-2',
      type: 'tool',
      name: 'nnU-Net Segmentation',
      x: 800,
      y: 50,
      status: 'running',
      confidence: 0.88,
      inputs: [
        { id: 'in-0', label: 'NIfTI Volume' },
        { id: 'in-1', label: 'Model Weights' }
      ],
      outputs: [
        { id: 'out-0', label: 'Segmentation Mask' }
      ]
    },
    {
      id: 'model-1',
      type: 'model',
      name: 'nnU-Net Pretrained Weights',
      x: 450,
      y: 320,
      outputs: [
        { id: 'out-0', label: 'Weights' }
      ]
    },
    {
      id: 'tool-3',
      type: 'tool',
      name: 'Post-processing',
      x: 1150,
      y: 50,
      status: 'pending',
      confidence: 0.92,
      inputs: [
        { id: 'in-0', label: 'Segmentation Mask' }
      ],
      outputs: [
        { id: 'out-0', label: 'Refined Mask' }
      ]
    },
    {
      id: 'output-1',
      type: 'measurement',
      role: 'output',
      name: 'Output Measurements',
      x: 1500,
      y: 50,
      inputs: [
        { id: 'in-0', label: 'Result', datasetId: 'tumor-segmentation', sampleId: 'Subject_001/tumor_mask.nii.gz' }
      ]
    }
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white min-h-0">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-white flex-shrink-0">
        <div>
          <span className="text-sm font-medium text-slate-700">3. Assemble, Review, and Validate Workflow</span>
          <p className="text-xs text-slate-500 mt-0.5">CWL Workflow Assembly & Validation</p>
        </div>
        
        {/* Workflow Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-slate-700">Subjects:</label>
            <input
              type="number"
              min="1"
              max="384"
              value={numSubjects}
              onChange={(e) => setNumSubjects(parseInt(e.target.value) || 1)}
              className="w-16 px-2 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-xs text-slate-500">/ 384</span>
          </div>
          <div className="w-px h-6 bg-slate-200"></div>
          <div className="flex items-center gap-2">
            {!isRunning ? (
              <button
                onClick={handleRunWorkflow}
                className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5" />
                Run Workflow
              </button>
            ) : (
              <button
                onClick={() => setIsRunning(false)}
                className="px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded hover:bg-red-700 transition-colors flex items-center gap-1.5"
              >
                <Square className="w-3.5 h-3.5" />
                Stop
              </button>
            )}
            <button className="px-3 py-1.5 border border-slate-300 text-slate-700 text-xs font-medium rounded hover:bg-slate-50 transition-colors flex items-center gap-1.5">
              <Download className="w-3.5 h-3.5" />
              Export Workflow (CWL)
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area with 3 horizontal panels */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Viewer Panel (Resizable & Collapsible) */}
        {!isViewerCollapsed ? (
          <ResizablePanel
            side="left"
            defaultWidth={400}
            minWidth={300}
            maxWidth={600}
          >
            <div className="h-full overflow-hidden bg-white relative">
              {/* Header with collapse button */}
              <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-white flex-shrink-0">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsViewerCollapsed(true)}
                    className="text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="text-sm font-medium text-slate-700">Document Viewer</span>
                </div>
              </div>

              {/* Content */}
              <div className="h-full overflow-hidden" style={{ paddingTop: '52px' }}>
                <ViewerPanel 
                  pdfUrl={isViewerVisible ? viewerPdfUrl : undefined}
                  onClose={onViewerClose}
                  activePropertyId={activePropertyId}
                />
              </div>
            </div>
          </ResizablePanel>
        ) : (
          /* Collapsed viewer */
          <div className="w-8 bg-slate-50 border-r border-slate-200 flex-shrink-0">
            <button
              onClick={() => setIsViewerCollapsed(false)}
              className="h-full w-full hover:bg-slate-100 transition-colors flex items-center justify-center"
            >
              <span className="text-xs font-medium text-slate-600 whitespace-nowrap" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
                Document Viewer
              </span>
            </button>
          </div>
        )}

        {/* Stage - Canvas (Center, flexible) */}
        <div 
          ref={canvasRef}
          className="flex-1 overflow-auto bg-slate-50 relative min-w-0"
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <div className="relative" style={{ width: '1600px', height: '600px' }}>
            {/* Connection Lines */}
            <svg className="absolute inset-0 pointer-events-none" style={{ width: '100%', height: '100%' }}>
              {connections.map(conn => {
                const sourceNode = nodes.find(n => n.id === conn.sourceNodeId);
                const targetNode = nodes.find(n => n.id === conn.targetNodeId);
                const sourcePort = sourceNode?.outputs?.find(p => p.id === conn.sourcePortId);
                const targetPort = targetNode?.inputs?.find(p => p.id === conn.targetPortId);
                
                if (!sourceNode || !targetNode || !sourcePort || !targetPort) return null;

                const sourcePortIndex = sourceNode.outputs?.indexOf(sourcePort) || 0;
                const targetPortIndex = targetNode.inputs?.indexOf(targetPort) || 0;

                return (
                  <ConnectionLine
                    key={conn.id}
                    id={conn.id}
                    sourceNode={sourceNode}
                    targetNode={targetNode}
                    sourcePortIndex={sourcePortIndex}
                    targetPortIndex={targetPortIndex}
                    onDelete={handleDeleteConnection}
                  />
                );
              })}
              
              {/* Drag Connection */}
              {dragConnection && (() => {
                const sourceNode = nodes.find(n => n.id === dragConnection.sourceNodeId);
                const sourcePort = sourceNode?.outputs?.find(p => p.id === dragConnection.sourcePortId);
                if (!sourceNode || !sourcePort) return null;
                
                const sourcePortIndex = sourceNode.outputs?.indexOf(sourcePort) || 0;
                const startX = sourceNode.x + 280;
                const startY = sourceNode.y + 70 + sourcePortIndex * 28;
                
                return (
                  <path
                    d={`M ${startX} ${startY} C ${startX + 100} ${startY}, ${dragConnection.x - 100} ${dragConnection.y}, ${dragConnection.x} ${dragConnection.y}`}
                    stroke="#3b82f6"
                    strokeWidth="2"
                    fill="none"
                    strokeDasharray="5,5"
                  />
                );
              })()}
            </svg>

            {/* Nodes */}
            {nodes.map(node => (
              <GraphNode
                key={node.id}
                node={node}
                isSelected={selectedNode?.id === node.id}
                onSelect={() => {
                  onSelectNode(node);
                  // Clear dataset selection when clicking on non-measurement nodes
                  if (node.type !== 'measurement' && onDatasetSelect) {
                    onDatasetSelect(null);
                  }
                }}
                onPortMouseDown={handlePortMouseDown}
                onPortMouseUp={handlePortMouseUp}
                onDatasetSelect={onDatasetSelect}
                selectedDatasetId={selectedDatasetId}
              />
            ))}
          </div>
        </div>

        {/* Data Object Catalogue (Resizable & Collapsible) */}
        {!isCatalogueCollapsed ? (
          <ResizablePanel
            side="right"
            defaultWidth={320}
            minWidth={280}
            maxWidth={500}
          >
            <div className="h-full overflow-hidden bg-white relative">
              {/* Content */}
              <div className="h-full overflow-hidden">
                <DataObjectCatalogue 
                  activeWorkflow={true} 
                  onSourceClick={onCatalogueSourceClick}
                  selectedNodeId={selectedNode?.id}
                  onDatasetSelect={onDatasetSelect}
                  selectedDatasetId={selectedDatasetId}
                  onCollapse={() => setIsCatalogueCollapsed(true)}
                />
              </div>
            </div>
          </ResizablePanel>
        ) : (
          /* Collapsed catalogue */
          <div className="w-8 bg-slate-50 border-l border-slate-200 flex-shrink-0">
            <button
              onClick={() => setIsCatalogueCollapsed(false)}
              className="h-full w-full hover:bg-slate-100 transition-colors flex items-center justify-center"
            >
              <span className="text-xs font-medium text-slate-600 whitespace-nowrap" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
                Data Object Catalogue
              </span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}