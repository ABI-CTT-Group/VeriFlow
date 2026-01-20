import { useState } from 'react';
import { Database, Beaker, Box, CheckCircle, Loader, Clock, AlertCircle, Plus, X, ChevronUp, ChevronDown } from 'lucide-react';

interface GraphNodeProps {
  node: any;
  isSelected: boolean;
  onSelect: () => void;
  onPortMouseDown: (nodeId: string, portId: string, portType: 'input' | 'output', event: React.MouseEvent) => void;
  onPortMouseUp: (nodeId: string, portId: string, portType: 'input' | 'output') => void;
}

const availableDatasets = [
  { id: 'dce-mri-scans', name: 'DCE-MRI Scans', samples: ['Subject_001/T1w.nii.gz', 'Subject_002/T1w.nii.gz', 'Subject_003/T1w.nii.gz'] },
  { id: 'tumor-segmentation', name: 'Tumor Segmentation', samples: ['Subject_001/tumor_mask.nii.gz', 'Subject_002/tumor_mask.nii.gz'] }
];

export function GraphNode({ node, isSelected, onSelect, onPortMouseDown, onPortMouseUp }: GraphNodeProps) {
  const [editingPort, setEditingPort] = useState<string | null>(null);

  const getSampleDisplayName = (samplePath: string) => {
    // Extract just the filename from the path
    return samplePath.split('/').pop() || samplePath;
  };

  const getStatusIcon = () => {
    if (node.type !== 'tool') return null;

    switch (node.status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'running':
        return <Loader className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-slate-400" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return null;
    }
  };

  const getNodeIcon = () => {
    switch (node.type) {
      case 'measurement':
        return <Database className="w-5 h-5 text-blue-600" />;
      case 'tool':
        return <Beaker className="w-5 h-5 text-purple-600" />;
      case 'model':
        return <Box className="w-5 h-5 text-green-600" />;
    }
  };

  const getStatusColor = () => {
    if (node.type !== 'tool') return 'border-slate-300';
    
    switch (node.status) {
      case 'completed':
        return 'border-green-300 bg-green-50';
      case 'running':
        return 'border-blue-300 bg-blue-50';
      case 'error':
        return 'border-red-300 bg-red-50';
      default:
        return 'border-slate-300';
    }
  };

  return (
    <div
      onClick={onSelect}
      className={`absolute bg-white rounded-lg border-2 cursor-pointer transition-all ${
        isSelected ? 'border-blue-500 shadow-lg' : getStatusColor()
      }`}
      style={{ 
        left: `${node.x}px`, 
        top: `${node.y}px`,
        width: '280px'
      }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {getNodeIcon()}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{node.name}</p>
              {node.confidence && (
                <p className="text-xs text-slate-500 mt-0.5">
                  Confidence: {(node.confidence * 100).toFixed(0)}%
                </p>
              )}
              {node.totalSubjects && (
                <p className="text-xs text-slate-500 mt-0.5">
                  {node.totalSubjects} subjects available
                </p>
              )}
            </div>
          </div>
          {getStatusIcon()}
        </div>
      </div>

      {/* Body */}
      <div className="p-3">
        {/* Input Ports */}
        {node.inputs && node.inputs.length > 0 && (
          <div className="space-y-2 mb-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-slate-600">Inputs</p>
              {node.role === 'output' && (
                <button 
                  className="text-slate-400 hover:text-slate-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Add new input handler
                  }}
                >
                  <Plus className="w-3 h-3" />
                </button>
              )}
            </div>
            {node.inputs.map((input: any, index: number) => (
              <div key={input.id} className="relative">
                {input.datasetId ? (
                  <div className="border border-slate-200 rounded-lg p-2 bg-slate-50/50">
                    <div className="flex items-start gap-2 mb-2">
                      {/* Input Port Circle */}
                      <div
                        className="absolute -left-6 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-slate-400 bg-white cursor-pointer hover:border-blue-500 hover:bg-blue-50 z-10"
                        onMouseUp={() => onPortMouseUp(node.id, input.id, 'input')}
                        style={{ pointerEvents: 'auto' }}
                      />
                      <div className="flex-1 space-y-1.5">
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">Dataset</label>
                          <select 
                            className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                            value={input.datasetId}
                            onClick={(e) => e.stopPropagation()}
                          >
                            {availableDatasets.map(ds => (
                              <option key={ds.id} value={ds.id}>{ds.name}</option>
                            ))}
                          </select>
                        </div>
                        {input.sampleId && (
                          <div>
                            <label className="text-xs text-slate-500 block mb-1">Sample</label>
                            <select 
                              className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                              value={input.sampleId}
                              onClick={(e) => e.stopPropagation()}
                            >
                              {availableDatasets.find(ds => ds.id === input.datasetId)?.samples.map(sample => (
                                <option key={sample} value={sample}>{getSampleDisplayName(sample)}</option>
                              ))}
                            </select>
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col gap-1">
                        {index > 0 && (
                          <button 
                            className="text-slate-400 hover:text-slate-600 p-0.5"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Move up handler
                            }}
                          >
                            <ChevronUp className="w-3 h-3" />
                          </button>
                        )}
                        {index < node.inputs.length - 1 && (
                          <button 
                            className="text-slate-400 hover:text-slate-600 p-0.5"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Move down handler
                            }}
                          >
                            <ChevronDown className="w-3 h-3" />
                          </button>
                        )}
                        <button 
                          className="text-red-400 hover:text-red-600 p-0.5"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Remove handler
                          }}
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    {/* Input Port Circle */}
                    <div
                      className="absolute -left-6 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-slate-400 bg-white cursor-pointer hover:border-blue-500 hover:bg-blue-50 z-10"
                      onMouseUp={() => onPortMouseUp(node.id, input.id, 'input')}
                      style={{ pointerEvents: 'auto' }}
                    />
                    <div className="flex-1 text-xs px-2 py-1.5 bg-slate-50 border border-slate-200 rounded">
                      {input.label}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Output Ports */}
        {node.outputs && node.outputs.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-slate-600">Outputs</p>
              {node.role === 'input' && (
                <button 
                  className="text-slate-400 hover:text-slate-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Add new output handler
                  }}
                >
                  <Plus className="w-3 h-3" />
                </button>
              )}
            </div>
            {node.outputs.map((output: any, index: number) => (
              <div key={output.id} className="relative">
                {output.datasetId ? (
                  <div className="border border-slate-200 rounded-lg p-2 bg-slate-50/50">
                    <div className="flex items-start gap-2 mb-2">
                      <div className="flex-1 space-y-1.5">
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">Dataset</label>
                          <select 
                            className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                            value={output.datasetId}
                            onClick={(e) => e.stopPropagation()}
                          >
                            {availableDatasets.map(ds => (
                              <option key={ds.id} value={ds.id}>{ds.name}</option>
                            ))}
                          </select>
                        </div>
                        {output.sampleId && (
                          <div>
                            <label className="text-xs text-slate-500 block mb-1">Sample</label>
                            <select 
                              className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                              value={output.sampleId}
                              onClick={(e) => e.stopPropagation()}
                            >
                              {availableDatasets.find(ds => ds.id === output.datasetId)?.samples.map(sample => (
                                <option key={sample} value={sample}>{getSampleDisplayName(sample)}</option>
                              ))}
                            </select>
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col gap-1">
                        {index > 0 && (
                          <button 
                            className="text-slate-400 hover:text-slate-600 p-0.5"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Move up handler
                            }}
                          >
                            <ChevronUp className="w-3 h-3" />
                          </button>
                        )}
                        {index < node.outputs.length - 1 && (
                          <button 
                            className="text-slate-400 hover:text-slate-600 p-0.5"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Move down handler
                            }}
                          >
                            <ChevronDown className="w-3 h-3" />
                          </button>
                        )}
                        <button 
                          className="text-red-400 hover:text-red-600 p-0.5"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Remove handler
                          }}
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                      {/* Output Port Circle */}
                      <div
                        className="absolute -right-6 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-slate-400 bg-white cursor-pointer hover:border-blue-500 hover:bg-blue-50 z-10"
                        onMouseDown={(e) => onPortMouseDown(node.id, output.id, 'output', e)}
                        style={{ pointerEvents: 'auto' }}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <div className="flex-1 text-xs px-2 py-1.5 bg-slate-50 border border-slate-200 rounded">
                      {output.label}
                    </div>
                    {/* Output Port Circle */}
                    <div
                      className="absolute -right-6 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-slate-400 bg-white cursor-pointer hover:border-blue-500 hover:bg-blue-50 z-10"
                      onMouseDown={(e) => onPortMouseDown(node.id, output.id, 'output', e)}
                      style={{ pointerEvents: 'auto' }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}