import { useState, useRef, useCallback } from 'react';
import { Play, Square, Download } from 'lucide-react';
import { GraphNode } from './GraphNode';
import { ConnectionLine } from './ConnectionLine';

interface WorkflowAssemblerModuleProps {
  selectedAssay: string | null;
  onSelectNode: (node: any) => void;
  selectedNode: any;
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
  selectedNode 
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
  const canvasRef = useRef<HTMLDivElement>(null);

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

  if (!selectedAssay) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 bg-slate-50">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <p className="text-sm">Select an assay from Study Design to begin</p>
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
      y: 100,
      outputs: [
        { id: 'out-0', label: 'MRI Scan', datasetId: 'dce-mri-scans', sampleId: 'Subject_001/T1w.nii.gz' },
        { id: 'out-1', label: 'Metadata', datasetId: 'dce-mri-scans', sampleId: 'Subject_001/metadata.json' }
      ],
      totalSubjects: 384
    },
    {
      id: 'tool-1',
      type: 'tool',
      name: 'DICOM to NIfTI',
      x: 400,
      y: 80,
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
      x: 650,
      y: 150,
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
      x: 400,
      y: 300,
      outputs: [
        { id: 'out-0', label: 'Weights' }
      ]
    },
    {
      id: 'tool-3',
      type: 'tool',
      name: 'Post-processing',
      x: 950,
      y: 150,
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
      x: 1250,
      y: 150,
      inputs: [
        { id: 'in-0', label: 'Result', datasetId: 'tumor-segmentation', sampleId: 'Subject_001/tumor_mask.nii.gz' }
      ]
    }
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Toolbar */}
      <div className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="text-sm font-medium text-slate-900">Workflow Assembler</h3>
            <p className="text-xs text-slate-500">{getAssayName()}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`flex items-center gap-2 px-3 py-1.5 text-xs rounded ${
                isRunning
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isRunning ? (
                <>
                  <Square className="w-3 h-3" />
                  Abort
                </>
              ) : (
                <>
                  <Play className="w-3 h-3" />
                  Run All
                </>
              )}
            </button>
            <button className="flex items-center gap-2 px-3 py-1.5 text-xs border border-slate-300 rounded hover:bg-slate-50">
              <Download className="w-3 h-3" />
              Export
            </button>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-600">Subjects:</label>
            <input
              type="number"
              min="1"
              max={384}
              value={numSubjects}
              onChange={(e) => setNumSubjects(parseInt(e.target.value) || 1)}
              className="w-20 px-2 py-1 text-xs border border-slate-300 rounded"
            />
            <span className="text-xs text-slate-400">of 384</span>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Catalogue Sidebar */}
        <div className="w-64 border-r border-slate-200 bg-white overflow-auto">
          <CataloguePanel />
        </div>

        {/* Canvas */}
        <div 
          ref={canvasRef}
          className="flex-1 overflow-auto bg-slate-50 relative"
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
                onSelect={() => onSelectNode(node)}
                onPortMouseDown={handlePortMouseDown}
                onPortMouseUp={handlePortMouseUp}
              />
            ))}
          </div>
        </div>

        {/* Property Editor Sidebar */}
        <div className="w-80 border-l border-slate-200 bg-white overflow-auto">
          <PropertyEditorPanel selectedNode={selectedNode} />
        </div>
      </div>
    </div>
  );
}

function CataloguePanel() {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['measurements', 'tools', 'models']));

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const measurements = [
    {
      id: 'meas-1',
      name: 'MRI T1 Scans',
      description: '120 breast MRI scans, T1-weighted, DICOM format',
      icon: 'database'
    },
    {
      id: 'meas-2',
      name: 'Tumor Annotations',
      description: 'Expert-labeled segmentation masks, NIfTI format',
      icon: 'database'
    },
    {
      id: 'meas-3',
      name: 'Clinical Metadata',
      description: 'Patient demographics, tumor characteristics',
      icon: 'database'
    }
  ];

  const tools = [
    {
      id: 'tool-1',
      name: 'DICOM Converter',
      description: 'Converts DICOM to NIfTI format using dcm2niix',
      icon: 'tool'
    },
    {
      id: 'tool-2',
      name: 'Image Preprocessor',
      description: 'Normalization, registration, bias field correction',
      icon: 'tool'
    },
    {
      id: 'tool-3',
      name: 'Segmentation Engine',
      description: 'U-Net based tumor segmentation pipeline',
      icon: 'tool'
    },
    {
      id: 'tool-4',
      name: 'Quality Control',
      description: 'Automated QC checks for segmentation outputs',
      icon: 'tool'
    }
  ];

  const models = [
    {
      id: 'model-1',
      name: 'nnU-Net Weights',
      description: 'Pretrained weights for breast tumor segmentation',
      icon: 'box'
    },
    {
      id: 'model-2',
      name: 'ResNet Classifier',
      description: 'Tumor classification model weights',
      icon: 'box'
    }
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-slate-200">
        <h3 className="text-sm font-medium text-slate-900">Data Object Catalogue</h3>
        <p className="text-xs text-slate-500 mt-0.5">Drag items to workflow</p>
      </div>
      
      <div className="flex-1 overflow-auto">
        {/* Measurements Section */}
        <div className="border-b border-slate-200">
          <button
            onClick={() => toggleSection('measurements')}
            className="w-full flex items-center gap-2 px-4 py-3 hover:bg-slate-50 transition-colors"
          >
            <svg className="w-4 h-4 text-slate-400 transition-transform" style={{ transform: expandedSections.has('measurements') ? 'rotate(0deg)' : 'rotate(-90deg)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
            </svg>
            <span className="text-sm font-medium text-slate-900">Measurements</span>
            <span className="text-xs text-slate-500">({measurements.length})</span>
          </button>
          
          {expandedSections.has('measurements') && (
            <div className="px-3 pb-3 space-y-2">
              {measurements.map((item) => (
                <div
                  key={item.id}
                  className="flex items-start gap-2 p-3 bg-white border border-slate-200 rounded-lg hover:shadow-sm hover:border-blue-300 transition-all cursor-move group"
                  draggable
                >
                  <svg className="w-4 h-4 text-slate-300 group-hover:text-slate-400 mt-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9 3h2v2H9V3zm0 4h2v2H9V7zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm4-16h2v2h-2V3zm0 4h2v2h-2V7zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2z" />
                  </svg>
                  <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900">{item.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tools Section */}
        <div className="border-b border-slate-200">
          <button
            onClick={() => toggleSection('tools')}
            className="w-full flex items-center gap-2 px-4 py-3 hover:bg-slate-50 transition-colors"
          >
            <svg className="w-4 h-4 text-slate-400 transition-transform" style={{ transform: expandedSections.has('tools') ? 'rotate(0deg)' : 'rotate(-90deg)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
            <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-sm font-medium text-slate-900">Tools</span>
            <span className="text-xs text-slate-500">({tools.length})</span>
          </button>
          
          {expandedSections.has('tools') && (
            <div className="px-3 pb-3 space-y-2">
              {tools.map((item) => (
                <div
                  key={item.id}
                  className="flex items-start gap-2 p-3 bg-white border border-slate-200 rounded-lg hover:shadow-sm hover:border-purple-300 transition-all cursor-move group"
                  draggable
                >
                  <svg className="w-4 h-4 text-slate-300 group-hover:text-slate-400 mt-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9 3h2v2H9V3zm0 4h2v2H9V7zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm4-16h2v2h-2V3zm0 4h2v2h-2V7zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2z" />
                  </svg>
                  <svg className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900">{item.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Models Section */}
        <div className="border-b border-slate-200">
          <button
            onClick={() => toggleSection('models')}
            className="w-full flex items-center gap-2 px-4 py-3 hover:bg-slate-50 transition-colors"
          >
            <svg className="w-4 h-4 text-slate-400 transition-transform" style={{ transform: expandedSections.has('models') ? 'rotate(0deg)' : 'rotate(-90deg)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
            <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <span className="text-sm font-medium text-slate-900">Models</span>
            <span className="text-xs text-slate-500">({models.length})</span>
          </button>
          
          {expandedSections.has('models') && (
            <div className="px-3 pb-3 space-y-2">
              {models.map((item) => (
                <div
                  key={item.id}
                  className="flex items-start gap-2 p-3 bg-white border border-slate-200 rounded-lg hover:shadow-sm hover:border-green-300 transition-all cursor-move group"
                  draggable
                >
                  <svg className="w-4 h-4 text-slate-300 group-hover:text-slate-400 mt-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9 3h2v2H9V3zm0 4h2v2H9V7zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm4-16h2v2h-2V3zm0 4h2v2h-2V7zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2z" />
                  </svg>
                  <svg className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900">{item.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PropertyEditorPanel({ selectedNode }: { selectedNode: any }) {
  if (!selectedNode) {
    return (
      <div className="p-4 text-center text-slate-400">
        <p className="text-sm">Select a node to edit properties</p>
      </div>
    );
  }

  return (
    <div className="p-4">
      <h3 className="text-sm font-medium text-slate-700 mb-3">Property Editor</h3>
      <div className="space-y-3">
        <div>
          <label className="text-xs font-medium text-slate-700 block mb-1">Name</label>
          <input
            type="text"
            defaultValue={selectedNode.name}
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {selectedNode.confidence !== undefined && (
          <div>
            <label className="text-xs font-medium text-slate-700 block mb-1">Confidence</label>
            <input
              type="range"
              min="0"
              max="100"
              defaultValue={selectedNode.confidence * 100}
              className="w-full"
            />
            <p className="text-xs text-slate-500 mt-1">{(selectedNode.confidence * 100).toFixed(0)}%</p>
          </div>
        )}
      </div>
    </div>
  );
}