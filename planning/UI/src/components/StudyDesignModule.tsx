import { useState } from 'react';
import { FileText, BookOpen, FlaskConical, Layers, ChevronRight, ChevronDown, Plus, X } from 'lucide-react';

interface StudyDesignModuleProps {
  onSelectAssay: (assayId: string | null) => void;
  selectedAssay: string | null;
}

interface WorkflowStep {
  id: string;
  description: string;
}

export function StudyDesignModule({ onSelectAssay, selectedAssay }: StudyDesignModuleProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['root', 'inv-1', 'study-1']));
  const [assayName, setAssayName] = useState('U-Net Training Assay');
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([
    { id: 'step-1', description: 'Data acquisition: Collect 120 MRI scans' },
    { id: 'step-2', description: 'Preprocessing: DICOM to NIfTI conversion' },
    { id: 'step-3', description: 'Normalization: Z-score normalization' },
    { id: 'step-4', description: 'Training: U-Net model with Adam optimizer' },
    { id: 'step-5', description: 'Validation: 5-fold cross-validation' },
    { id: 'step-6', description: 'Evaluation: Calculate DICE scores' }
  ]);

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const handleNodeClick = (nodeId: string, type: string) => {
    if (type === 'assay') {
      onSelectAssay(nodeId === selectedAssay ? null : nodeId);
    }
  };

  const addStep = () => {
    const newStep: WorkflowStep = {
      id: `step-${Date.now()}`,
      description: 'New workflow step'
    };
    setWorkflowSteps([...workflowSteps, newStep]);
  };

  const removeStep = (stepId: string) => {
    setWorkflowSteps(workflowSteps.filter(s => s.id !== stepId));
  };

  const updateStep = (stepId: string, description: string) => {
    setWorkflowSteps(workflowSteps.map(s => 
      s.id === stepId ? { ...s, description } : s
    ));
  };

  const moveStep = (index: number, direction: 'up' | 'down') => {
    const newSteps = [...workflowSteps];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex >= 0 && targetIndex < newSteps.length) {
      [newSteps[index], newSteps[targetIndex]] = [newSteps[targetIndex], newSteps[index]];
      setWorkflowSteps(newSteps);
    }
  };

  return (
    <div className="flex-1 border-b border-slate-200 bg-white flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex flex-col border-b border-slate-200 px-4 py-2">
        <button className="flex items-center justify-between hover:bg-slate-50 transition-colors">
          <div className="text-left">
            <span className="text-sm font-medium text-slate-700">Study Design Selector</span>
            <p className="text-xs text-slate-500">ISA (Investigation, Study, Assay) Hierarchy</p>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400" />
        </button>
      </div>
      
      {/* Tree View */}
      <div className="px-3 py-3 space-y-1 border-b border-slate-200">
        <div className="space-y-1">
          <div
            className="flex items-center gap-2 p-2 rounded hover:bg-slate-50 cursor-pointer"
            onClick={() => toggleNode('root')}
          >
            {expandedNodes.has('root') ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
            <FileText className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-slate-900 truncate">
              Breast Cancer Segmentation Using Dee...
            </span>
          </div>

          {expandedNodes.has('root') && (
            <div className="ml-6 space-y-1">
              <div
                className="flex items-center gap-2 p-2 rounded hover:bg-slate-50 cursor-pointer"
                onClick={() => toggleNode('inv-1')}
              >
                {expandedNodes.has('inv-1') ? (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                )}
                <BookOpen className="w-4 h-4 text-green-600" />
                <span className="text-sm text-slate-700 truncate">Automated Tumor Detection Investig...</span>
              </div>

              {expandedNodes.has('inv-1') && (
                <div className="ml-6 space-y-1">
                  <div
                    className="flex items-center gap-2 p-2 rounded hover:bg-slate-50 cursor-pointer"
                    onClick={() => toggleNode('study-1')}
                  >
                    {expandedNodes.has('study-1') ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                    <Layers className="w-4 h-4 text-purple-600" />
                    <span className="text-sm text-slate-700">MRI-based Segmentation Study</span>
                  </div>

                  {expandedNodes.has('study-1') && (
                    <div className="ml-6 space-y-1">
                      <div
                        className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                          selectedAssay === 'assay-1'
                            ? 'bg-blue-50 border border-blue-200'
                            : 'hover:bg-slate-50'
                        }`}
                        onClick={() => handleNodeClick('assay-1', 'assay')}
                      >
                        <FlaskConical className="w-4 h-4 text-orange-600" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-sm text-slate-700">U-Net Training Assay</p>
                            <span className="text-xs text-slate-500">(6 steps)</span>
                          </div>
                        </div>
                      </div>

                      <div
                        className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                          selectedAssay === 'assay-2'
                            ? 'bg-blue-50 border border-blue-200'
                            : 'hover:bg-slate-50'
                        }`}
                        onClick={() => handleNodeClick('assay-2', 'assay')}
                      >
                        <FlaskConical className="w-4 h-4 text-orange-600" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-sm text-slate-700">Model Inference Assay</p>
                            <span className="text-xs text-slate-500">(4 steps)</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Property Editor - Shows when assay is selected */}
      {selectedAssay && (
        <div className="flex-1 overflow-auto">
          <div className="p-4 space-y-4">
            {/* Header */}
            <div className="border-b border-slate-200 pb-3">
              <h3 className="font-medium text-slate-900">Property Editor</h3>
              <p className="text-xs text-slate-500 mt-0.5">Assay Node</p>
            </div>

            {/* Name */}
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-2">Name</label>
              <input
                type="text"
                value={assayName}
                onChange={(e) => setAssayName(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Workflow Steps */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-slate-700">Workflow Steps</label>
                <button
                  onClick={addStep}
                  className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" />
                  Add Step
                </button>
              </div>
              
              <div className="space-y-2">
                {workflowSteps.map((step, index) => (
                  <div key={step.id} className="relative">
                    <div className="flex items-start gap-2">
                      <span className="text-xs text-slate-500 mt-2 w-6">{index + 1}.</span>
                      <input
                        type="text"
                        value={step.description}
                        onChange={(e) => updateStep(step.id, e.target.value)}
                        className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <div className="flex flex-col gap-1">
                        {index > 0 && (
                          <button
                            onClick={() => moveStep(index, 'up')}
                            className="text-slate-400 hover:text-slate-600 p-1"
                          >
                            <ChevronDown className="w-3 h-3 rotate-180" />
                          </button>
                        )}
                        {index < workflowSteps.length - 1 && (
                          <button
                            onClick={() => moveStep(index, 'down')}
                            className="text-slate-400 hover:text-slate-600 p-1"
                          >
                            <ChevronDown className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                      <button
                        onClick={() => removeStep(step.id)}
                        className="text-red-400 hover:text-red-600 p-1"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Save Button */}
            <button className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
              Save Changes
            </button>
          </div>
        </div>
      )}

      {/* Assemble Button */}
      <div className="border-t border-slate-200 p-3">
        <button
          disabled={!selectedAssay}
          className={`w-full px-4 py-2 text-sm rounded transition-colors ${
            selectedAssay
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        >
          Assemble Selected Assay
        </button>
      </div>
    </div>
  );
}
