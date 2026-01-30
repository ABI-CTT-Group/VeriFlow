import { useState, useEffect } from 'react';
import { FileText, BookOpen, FlaskConical, Layers, ChevronRight, ChevronDown, Plus, X, ExternalLink, ChevronLeft } from 'lucide-react';

interface StudyDesignModuleProps {
  onSelectAssay: (assayId: string | null) => void;
  selectedAssay: string | null;
  hasUploadedFiles: boolean;
  onSourceClick: (propertyId: string) => void;
  onAssembleClick?: () => void;
  isHorizontallyCollapsed?: boolean;
  onToggleHorizontalCollapse?: () => void;
  onCollapseLeftPanel?: () => void;
}

interface WorkflowStep {
  id: string;
  description: string;
}

type SelectedItem = {
  id: string;
  type: 'paper' | 'investigation' | 'study' | 'assay';
  name: string;
};

export function StudyDesignModule({ 
  onSelectAssay, 
  selectedAssay, 
  hasUploadedFiles,
  onSourceClick,
  onAssembleClick,
  isHorizontallyCollapsed,
  onToggleHorizontalCollapse,
  onCollapseLeftPanel
}: StudyDesignModuleProps) {
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['root', 'study-1']));
  // Initialize as expanded if files are already uploaded
  const [isExpanded, setIsExpanded] = useState(hasUploadedFiles);
  const [assayName, setAssayName] = useState('U-Net Training Assay');
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([
    { id: 'step-1', description: 'Data acquisition: Collect 120 MRI scans' },
    { id: 'step-2', description: 'Preprocessing: DICOM to NIfTI conversion' },
    { id: 'step-3', description: 'Normalization: Z-score normalization' },
    { id: 'step-4', description: 'Training: U-Net model with Adam optimizer' },
    { id: 'step-5', description: 'Validation: 5-fold cross-validation' },
    { id: 'step-6', description: 'Evaluation: Calculate DICE scores' }
  ]);

  // Paper properties
  const [paperTitle, setPaperTitle] = useState('Breast Cancer Segmentation Using Deep Learning');
  const [paperAuthors, setPaperAuthors] = useState('Smith, J., et al.');
  const [paperYear, setPaperYear] = useState('2023');
  const [paperAbstract, setPaperAbstract] = useState('This study presents a novel approach to automated breast cancer segmentation using deep learning techniques on DCE-MRI scans.');

  // Investigation properties
  const [investigationTitle, setInvestigationTitle] = useState('Automated Tumor Detection Investigation');
  const [investigationDescription, setInvestigationDescription] = useState('Investigation of automated deep learning methods for breast tumor detection and segmentation in DCE-MRI images');
  const [investigationSubmissionDate, setInvestigationSubmissionDate] = useState('2023-01-15');

  // Study properties
  const [studyTitle, setStudyTitle] = useState('MRI-based Segmentation Study');
  const [studyDescription, setStudyDescription] = useState('Comprehensive study of U-Net based segmentation on breast MRI scans');
  const [studyNumSubjects, setStudyNumSubjects] = useState('384');
  const [studyDesign, setStudyDesign] = useState('Retrospective cohort study');

  // Expand when files are uploaded
  useEffect(() => {
    if (hasUploadedFiles) {
      setIsExpanded(true);
    }
  }, [hasUploadedFiles]);

  const handleNodeClick = (id: string, type: 'paper' | 'investigation' | 'study' | 'assay', name: string, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    
    // Toggle selection - deselect if clicking the same item
    if (selectedItem?.id === id) {
      setSelectedItem(null);
      if (type === 'assay') {
        onSelectAssay(null);
      }
    } else {
      setSelectedItem({ id, type, name });
      // Update assay selection for backward compatibility
      if (type === 'assay') {
        onSelectAssay(id);
      } else {
        onSelectAssay(null);
      }
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

  const renderPropertyEditor = () => {
    if (!selectedItem) {
      return (
        <div className="p-4 text-center text-slate-400">
          <p className="text-sm">Select an item to edit properties</p>
        </div>
      );
    }

    // Paper Properties
    if (selectedItem.type === 'paper') {
      return (
        <div className="p-4 space-y-4">
          <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
            <div>
              <h3 className="font-medium text-slate-900">Paper Properties</h3>
              <p className="text-xs text-slate-500 mt-0.5">{selectedItem.name}</p>
            </div>
            <button
              onClick={() => setSelectedItem(null)}
              className="text-slate-400 hover:text-slate-600 transition-colors"
              title="Close property editor"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Title</label>
              <button
                onClick={() => onSourceClick('paper-title')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <input
              type="text"
              value={paperTitle}
              onChange={(e) => setPaperTitle(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Authors</label>
              <button
                onClick={() => onSourceClick('paper-authors')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <input
              type="text"
              value={paperAuthors}
              onChange={(e) => setPaperAuthors(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Publication Year</label>
              <button
                onClick={() => onSourceClick('paper-year')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <input
              type="text"
              value={paperYear}
              onChange={(e) => setPaperYear(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Abstract</label>
              <button
                onClick={() => onSourceClick('paper-abstract')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <textarea
              value={paperAbstract}
              onChange={(e) => setPaperAbstract(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
            />
          </div>

          <button className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
            Save Changes
          </button>
        </div>
      );
    }

    // Investigation Properties
    if (selectedItem.type === 'investigation') {
      return (
        <div className="p-4 space-y-4">
          <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
            <div>
              <h3 className="font-medium text-slate-900">Investigation Properties</h3>
              <p className="text-xs text-slate-500 mt-0.5">{selectedItem.name}</p>
            </div>
            <button
              onClick={() => setSelectedItem(null)}
              className="text-slate-400 hover:text-slate-600 transition-colors"
              title="Close property editor"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Title</label>
              <button
                onClick={() => onSourceClick('inv-title')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <input
              type="text"
              value={investigationTitle}
              onChange={(e) => setInvestigationTitle(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Description</label>
              <button
                onClick={() => onSourceClick('inv-description')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <textarea
              value={investigationDescription}
              onChange={(e) => setInvestigationDescription(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Submission Date</label>
              <button
                onClick={() => onSourceClick('inv-date')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <input
              type="date"
              value={investigationSubmissionDate}
              onChange={(e) => setInvestigationSubmissionDate(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
            Save Changes
          </button>
        </div>
      );
    }

    // Study Properties
    if (selectedItem.type === 'study') {
      return (
        <div className="p-4 space-y-4">
          <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
            <div>
              <h3 className="font-medium text-slate-900">Study Properties</h3>
              <p className="text-xs text-slate-500 mt-0.5">{selectedItem.name}</p>
            </div>
            <button
              onClick={() => setSelectedItem(null)}
              className="text-slate-400 hover:text-slate-600 transition-colors"
              title="Close property editor"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Study Title</label>
              <button
                onClick={() => onSourceClick('study-title')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <input
              type="text"
              value={studyTitle}
              onChange={(e) => setStudyTitle(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Description</label>
              <button
                onClick={() => onSourceClick('study-description')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <textarea
              value={studyDescription}
              onChange={(e) => setStudyDescription(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Number of Subjects</label>
              <button
                onClick={() => onSourceClick('study-subjects')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <input
              type="number"
              value={studyNumSubjects}
              onChange={(e) => setStudyNumSubjects(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Study Design</label>
              <button
                onClick={() => onSourceClick('study-design')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <select
              value={studyDesign}
              onChange={(e) => setStudyDesign(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option>Retrospective cohort study</option>
              <option>Prospective cohort study</option>
              <option>Case-control study</option>
              <option>Cross-sectional study</option>
              <option>Randomized controlled trial</option>
            </select>
          </div>

          <button className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
            Save Changes
          </button>
        </div>
      );
    }

    // Assay Properties
    if (selectedItem.type === 'assay') {
      return (
        <div className="p-4 space-y-4">
          <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
            <div>
              <h3 className="font-medium text-slate-900">Assay Properties</h3>
              <p className="text-xs text-slate-500 mt-0.5">{selectedItem.name}</p>
            </div>
            <button
              onClick={() => setSelectedItem(null)}
              className="text-slate-400 hover:text-slate-600 transition-colors"
              title="Close property editor"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-700">Name</label>
              <button
                onClick={() => onSourceClick('assay-name')}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            </div>
            <input
              type="text"
              value={assayName}
              onChange={(e) => setAssayName(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

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
                    <button
                      onClick={() => onSourceClick(`step-${step.id}`)}
                      className="text-blue-600 hover:text-blue-700 p-2"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => removeStep(step.id)}
                      className="text-red-400 hover:text-red-600 p-2"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
            Save Changes
          </button>
        </div>
      );
    }

    return null;
  };

  if (!isExpanded) {
    return (
      <div className="border-b border-slate-200 bg-white">
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-center gap-2 flex-1">
            {onCollapseLeftPanel && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onCollapseLeftPanel();
                }}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}
            <div className="text-left">
              <span className="text-sm font-medium text-slate-700">2. Review Study Design</span>
              <p className="text-xs text-slate-500">ISA (Investigation, Study, Assay) Hierarchy</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 border-b border-slate-200 bg-white flex flex-col overflow-hidden">
      {/* Header with both collapse buttons */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors ${
          isExpanded ? 'border-b border-slate-200' : ''
        }`}
      >
        <div className="flex items-center gap-2 flex-1">
          {onCollapseLeftPanel && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onCollapseLeftPanel();
              }}
              className="text-slate-400 hover:text-slate-600 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          )}
          <div className="text-left">
            <span className="text-sm font-medium text-slate-700">2. Review Study Design</span>
            <p className="text-xs text-slate-500">ISA (Investigation, Study, Assay) Hierarchy</p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-400" />
        )}
      </button>
      {isExpanded && (
        <>
      {/* Tree View - Only show when files are uploaded */}
      {hasUploadedFiles ? (
        <div className="px-3 py-3 space-y-1 border-b border-slate-200 overflow-auto flex-shrink-0">
          <div className="space-y-1">
            <div
              className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                selectedItem?.id === 'root' ? 'bg-blue-50 border border-blue-200' : 'hover:bg-slate-50'
              }`}
              onClick={(e) => {
                handleNodeClick('root', 'paper', 'Breast Cancer Segmentation Using Deep Learning', e);
              }}
            >
              <FileText className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-slate-900 truncate">
                Breast Cancer Segmentation Using Dee...
              </span>
            </div>

            <div className="ml-6 space-y-1">
              <div
                className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                  selectedItem?.id === 'inv-1' ? 'bg-blue-50 border border-blue-200' : 'hover:bg-slate-50'
                }`}
                onClick={(e) => {
                  handleNodeClick('inv-1', 'investigation', 'Automated Tumor Detection Investigation', e);
                }}
              >
                <BookOpen className="w-4 h-4 text-green-600" />
                <span className="text-sm text-slate-700 truncate">Automated Tumor Detection Investig...</span>
              </div>

              <div className="ml-6 space-y-1">
                <div
                  className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                    selectedItem?.id === 'study-1' ? 'bg-blue-50 border border-blue-200' : 'hover:bg-slate-50'
                  }`}
                  onClick={(e) => {
                    handleNodeClick('study-1', 'study', 'MRI-based Segmentation Study', e);
                  }}
                >
                  <Layers className="w-4 h-4 text-purple-600" />
                  <span className="text-sm text-slate-700">MRI-based Segmentation Study</span>
                </div>

                <div className="ml-6 space-y-1">
                  <div
                    className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                      selectedItem?.id === 'assay-1'
                        ? 'bg-blue-50 border border-blue-200'
                        : 'hover:bg-slate-50'
                    }`}
                    onClick={(e) => handleNodeClick('assay-1', 'assay', 'U-Net Training Assay', e)}
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
                      selectedItem?.id === 'assay-2'
                        ? 'bg-blue-50 border border-blue-200'
                        : 'hover:bg-slate-50'
                    }`}
                    onClick={(e) => handleNodeClick('assay-2', 'assay', 'Model Inference Assay', e)}
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
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-slate-400 bg-slate-50">
          <div className="text-center px-4">
            <svg className="w-10 h-10 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-xs">Upload a publication to begin</p>
          </div>
        </div>
      )}

      {/* Property Editor - Shows when any item is selected and files are uploaded */}
      {hasUploadedFiles && (
        <div className="flex-1 overflow-auto border-t border-slate-200">
          {renderPropertyEditor()}
        </div>
      )}

      {/* Assemble Button - Only show when an assay is selected */}
      {selectedAssay && hasUploadedFiles && (
        <div className="border-t border-slate-200 p-3 flex-shrink-0">
          <button
            className="w-full px-4 py-2 text-sm rounded transition-colors bg-blue-600 text-white hover:bg-blue-700"
            onClick={onAssembleClick}
          >
            Assemble Selected Assay
          </button>
        </div>
      )}
        </>
      )}
    </div>
  );
}