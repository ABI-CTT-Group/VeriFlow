import { Database, Beaker, Box, Plus, CheckCircle, Loader, Clock, AlertCircle } from 'lucide-react';

interface WorkflowNodeProps {
  node: any;
  isSelected: boolean;
  onSelect: () => void;
  nodeType: 'input' | 'output' | 'tool' | 'model';
}

export function WorkflowNode({ node, isSelected, onSelect, nodeType }: WorkflowNodeProps) {
  const getStatusIcon = () => {
    if (nodeType === 'input' || nodeType === 'output' || nodeType === 'model') {
      return null;
    }

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
    switch (nodeType) {
      case 'input':
      case 'output':
        return <Database className="w-5 h-5 text-blue-600" />;
      case 'tool':
        return <Beaker className="w-5 h-5 text-purple-600" />;
      case 'model':
        return <Box className="w-5 h-5 text-green-600" />;
    }
  };

  const getStatusColor = () => {
    if (nodeType !== 'tool') return 'border-slate-300';
    
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
      className={`bg-white rounded-lg border-2 cursor-pointer transition-all ${
        isSelected ? 'border-blue-500 shadow-lg' : getStatusColor()
      } ${nodeType === 'model' ? 'w-48' : 'w-64'}`}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 flex-1">
            {getNodeIcon()}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{node.name}</p>
              {nodeType === 'tool' && node.confidence && (
                <p className="text-xs text-slate-500 mt-0.5">
                  Confidence: {(node.confidence * 100).toFixed(0)}%
                </p>
              )}
            </div>
          </div>
          {getStatusIcon()}
        </div>
      </div>

      {/* Body */}
      <div className="p-3 space-y-2">
        {/* Inputs */}
        {(nodeType === 'tool' || nodeType === 'input') && node.inputs && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-xs font-medium text-slate-600">
                {nodeType === 'input' ? 'Samples' : 'Inputs'}
              </p>
              <button className="text-slate-400 hover:text-slate-600">
                <Plus className="w-3 h-3" />
              </button>
            </div>
            <div className="space-y-1">
              {node.inputs.map((input: string, index: number) => (
                <div
                  key={index}
                  className="text-xs px-2 py-1 bg-slate-50 border border-slate-200 rounded truncate"
                >
                  {input}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Samples for measurements */}
        {(nodeType === 'input' || nodeType === 'output') && node.samples && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-xs font-medium text-slate-600">Samples</p>
              <button className="text-slate-400 hover:text-slate-600">
                <Plus className="w-3 h-3" />
              </button>
            </div>
            <div className="space-y-1 max-h-24 overflow-y-auto">
              {node.samples.map((sample: string, index: number) => (
                <div
                  key={index}
                  className="text-xs px-2 py-1 bg-slate-50 border border-slate-200 rounded truncate"
                >
                  {sample}
                </div>
              ))}
            </div>
            {node.totalSubjects && (
              <p className="text-xs text-slate-500 mt-1">
                Total: {node.totalSubjects} subjects available
              </p>
            )}
          </div>
        )}

        {/* Outputs */}
        {(nodeType === 'tool' || nodeType === 'output') && node.outputs && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-xs font-medium text-slate-600">Outputs</p>
              <button className="text-slate-400 hover:text-slate-600">
                <Plus className="w-3 h-3" />
              </button>
            </div>
            <div className="space-y-1">
              {node.outputs.map((output: string, index: number) => (
                <div
                  key={index}
                  className="text-xs px-2 py-1 bg-slate-50 border border-slate-200 rounded truncate"
                >
                  {output}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Model specific */}
        {nodeType === 'model' && (
          <div>
            <p className="text-xs text-slate-500">Connected to Tool {node.connectedTo?.split('-')[1]}</p>
          </div>
        )}
      </div>
    </div>
  );
}
