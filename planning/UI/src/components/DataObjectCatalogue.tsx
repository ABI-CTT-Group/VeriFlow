import { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, ExternalLink, Minimize2 } from 'lucide-react';

interface DataObjectCatalogueProps {
  activeWorkflow?: boolean;
  onSourceClick?: (propertyId: string) => void;
  selectedNodeId?: string;
  onDatasetSelect?: (datasetId: string) => void;
  selectedDatasetId?: string;
  onCollapse?: () => void;
}

export function DataObjectCatalogue({ activeWorkflow = false, onSourceClick, selectedNodeId, onDatasetSelect, selectedDatasetId, onCollapse }: DataObjectCatalogueProps) {
  const [activeTab, setActiveTab] = useState<'active' | 'all'>('active');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [expandedItem, setExpandedItem] = useState<string | null>(null);

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const toggleItem = (itemId: string) => {
    setExpandedItem(expandedItem === itemId ? null : itemId);
  };

  // Active data objects from current workflow
  const activeInputMeasurements = [
    {
      id: 'meas-active-1',
      name: 'DCE-MRI Scans',
      description: '384 subjects, T1-weighted, DICOM format',
      icon: 'database',
      inUse: true
    }
  ];

  const activeOutputMeasurements = [
    {
      id: 'meas-active-2',
      name: 'Tumor Segmentation Masks',
      description: 'Ground truth annotations, NIfTI format',
      icon: 'database',
      inUse: true
    }
  ];

  const activeTools = [
    {
      id: 'tool-active-1',
      name: 'DICOM to NIfTI',
      description: 'Converts DICOM to NIfTI using dcm2niix',
      icon: 'tool',
      inUse: true
    },
    {
      id: 'tool-active-2',
      name: 'nnU-Net Segmentation',
      description: 'U-Net based tumor segmentation',
      icon: 'tool',
      inUse: true
    },
    {
      id: 'tool-active-3',
      name: 'Post-processing',
      description: 'Refines segmentation masks',
      icon: 'tool',
      inUse: true
    }
  ];

  const activeModels = [
    {
      id: 'model-active-1',
      name: 'nnU-Net Pretrained Weights',
      description: 'Pretrained on medical imaging datasets',
      icon: 'box',
      inUse: true
    }
  ];

  // All available data objects
  const allInputMeasurements = [
    ...activeInputMeasurements,
    {
      id: 'meas-3',
      name: 'Clinical Metadata',
      description: 'Patient demographics, tumor characteristics',
      icon: 'database',
      inUse: false
    }
  ];

  const allOutputMeasurements = [
    ...activeOutputMeasurements,
    {
      id: 'meas-2',
      name: 'CT Segmentation Results',
      description: 'Segmentation outputs from CT scans',
      icon: 'database',
      inUse: false
    }
  ];

  const allTools = [
    ...activeTools,
    {
      id: 'tool-3',
      name: 'Image Preprocessor',
      description: 'Normalization, registration, bias correction',
      icon: 'tool',
      inUse: false
    },
    {
      id: 'tool-4',
      name: 'Quality Control',
      description: 'Automated QC checks for outputs',
      icon: 'tool',
      inUse: false
    }
  ];

  const allModels = [
    ...activeModels,
    {
      id: 'model-2',
      name: 'ResNet Classifier',
      description: 'Tumor classification model',
      icon: 'box',
      inUse: false
    }
  ];

  const inputMeasurements = activeTab === 'active' ? activeInputMeasurements : allInputMeasurements;
  const outputMeasurements = activeTab === 'active' ? activeOutputMeasurements : allOutputMeasurements;
  const tools = activeTab === 'active' ? activeTools : allTools;
  const models = activeTab === 'active' ? activeModels : allModels;

  // Map workflow nodes to data object IDs
  const nodeToDataObjectMap: Record<string, string> = {
    'input-1': 'meas-active-1',
    'output-1': 'meas-active-2',
    'tool-1': 'tool-active-1',
    'tool-2': 'tool-active-2',
    'tool-3': 'tool-active-3',
    'model-1': 'model-active-1'
  };

  // Map dataset IDs to data object IDs
  const datasetToDataObjectMap: Record<string, string> = {
    'dce-mri-scans': 'meas-active-1',
    'tumor-segmentation': 'meas-active-2'
  };

  // Auto-expand and edit when a node is selected
  useEffect(() => {
    if (selectedNodeId) {
      const dataObjectId = nodeToDataObjectMap[selectedNodeId];
      if (dataObjectId) {
        // Determine which section the data object belongs to
        const allData = [...inputMeasurements, ...outputMeasurements, ...tools, ...models];
        const dataObject = allData.find(obj => obj.id === dataObjectId);
        
        if (dataObject) {
          // Expand the appropriate section
          let sectionId = '';
          if (inputMeasurements.find(m => m.id === dataObjectId)) {
            sectionId = 'input-measurements';
          } else if (outputMeasurements.find(m => m.id === dataObjectId)) {
            sectionId = 'output-measurements';
          } else if (tools.find(t => t.id === dataObjectId)) {
            sectionId = 'tools';
          } else if (models.find(m => m.id === dataObjectId)) {
            sectionId = 'models';
          }
          
          if (sectionId) {
            setExpandedSections(new Set([sectionId]));
            setExpandedItem(dataObjectId);
          }
        }
      }
    }
  }, [selectedNodeId]);

  // Auto-expand and highlight when dataset is selected
  useEffect(() => {
    if (selectedDatasetId) {
      // Map dataset ID to data object ID
      const dataObjectId = datasetToDataObjectMap[selectedDatasetId];
      
      if (dataObjectId) {
        // Find which section contains this data object
        const allInputs = [...activeInputMeasurements, ...allInputMeasurements];
        const allOutputs = [...activeOutputMeasurements, ...allOutputMeasurements];
        
        const inputDataset = allInputs.find(d => d.id === dataObjectId);
        const outputDataset = allOutputs.find(d => d.id === dataObjectId);
        
        if (inputDataset) {
          // Expand the Input Measurements section
          const newExpanded = new Set(expandedSections);
          newExpanded.add('input-measurements');
          setExpandedSections(newExpanded);
          
          // Expand the specific item
          setExpandedItem(dataObjectId);
        } else if (outputDataset) {
          // Expand the Output Measurements section
          const newExpanded = new Set(expandedSections);
          newExpanded.add('output-measurements');
          setExpandedSections(newExpanded);
          
          // Expand the specific item
          setExpandedItem(dataObjectId);
        }
      }
    }
  }, [selectedDatasetId]);

  const handleCollapseAll = () => {
    setExpandedSections(new Set());
    setExpandedItem(null);
    if (onCollapse) {
      onCollapse();
    }
  };

  const renderPropertyEditor = (item: any) => (
    <div className="mx-3 mb-2 bg-white border border-slate-200 rounded-lg overflow-hidden">
      {/* Header showing which item is being edited */}
      <div className="px-3 py-2 bg-slate-100 border-b border-slate-200 flex items-center gap-2">
        <div className="flex items-center gap-2 flex-1">
          <svg className="w-4 h-4 text-slate-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M9 3h2v2H9V3zm0 4h2v2H9V7zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm4-16h2v2h-2V3zm0 4h2v2h-2V7zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2z" />
          </svg>
          <span className="text-xs font-medium text-slate-700">Editing: {item.name}</span>
        </div>
        {item.inUse && (
          <span className="px-1.5 py-0.5 text-xs bg-green-100 text-green-700 rounded">In Use</span>
        )}
      </div>
      
      {/* Property fields */}
      <div className="p-3 space-y-3 bg-white">
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-medium text-slate-700">Name</label>
            {onSourceClick && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSourceClick(`${item.id}-name`);
                }}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            )}
          </div>
          <input
            type="text"
            defaultValue={item.name}
            className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          />
        </div>
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-medium text-slate-700">Description</label>
            {onSourceClick && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSourceClick(`${item.id}-description`);
                }}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            )}
          </div>
          <textarea
            defaultValue={item.description}
            className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            rows={3}
          />
        </div>
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-medium text-slate-700">Type</label>
            {onSourceClick && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSourceClick(`${item.id}-type`);
                }}
                className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                Source
              </button>
            )}
          </div>
          <select className="w-full px-2 py-1.5 text-xs border border-slate-300 rounded hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
            <option>{item.icon}</option>
          </select>
        </div>
        <button className="w-full px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors">
          Save Changes
        </button>
      </div>
    </div>
  );

  const renderDataObjectSection = (
    title: string,
    items: any[],
    sectionId: string,
    iconColor: string,
    IconComponent: any
  ) => (
    <div className="border-b border-slate-200">
      <button
        onClick={() => toggleSection(sectionId)}
        className="w-full flex items-center gap-2 px-4 py-3 hover:bg-slate-50 transition-colors"
      >
        <svg 
          className="w-4 h-4 text-slate-400 transition-transform" 
          style={{ transform: expandedSections.has(sectionId) ? 'rotate(0deg)' : 'rotate(-90deg)' }} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
        <IconComponent className={`w-4 h-4 ${iconColor}`} />
        <span className="text-sm font-medium text-slate-900">{title}</span>
        <span className="text-xs text-slate-500">({items.length})</span>
      </button>
      
      {expandedSections.has(sectionId) && (
        <div className="pb-2">
          {items.map((item) => (
            <div key={item.id}>
              <div
                className="mx-3 mb-2 bg-white border border-slate-200 rounded-lg overflow-hidden hover:shadow-sm hover:border-blue-300 transition-all cursor-pointer"
                onClick={() => toggleItem(item.id)}
              >
                <div className="flex items-start gap-2 p-3">
                  <svg className="w-4 h-4 text-slate-300 mt-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9 3h2v2H9V3zm0 4h2v2H9V7zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm0 4h2v2H9v-2zm4-16h2v2h-2V3zm0 4h2v2h-2V7zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2z" />
                  </svg>
                  <IconComponent className={`w-5 h-5 ${iconColor} mt-0.5 flex-shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-slate-900">{item.name}</p>
                      {item.inUse && (
                        <span className="px-1.5 py-0.5 text-xs bg-green-100 text-green-700 rounded">In Use</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>
                  </div>
                  {expandedItem === item.id ? (
                    <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  )}
                </div>
              </div>
              {expandedItem === item.id && renderPropertyEditor(item)}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const DatabaseIcon = ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
    </svg>
  );

  const ToolIcon = ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );

  const BoxIcon = ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    </svg>
  );

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header with Tabs */}
      <div className="border-b border-slate-200">
        <div className="p-4 flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-slate-900">Data Object Catalogue</h3>
            <p className="text-xs text-slate-500 mt-0.5">Browse and edit data objects</p>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleCollapseAll}
              className="px-2 py-1 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded transition-colors flex items-center gap-1"
              title="Collapse all sections"
            >
              <Minimize2 className="w-3 h-3" />
              Collapse All
            </button>
            {onCollapse && (
              <button
                onClick={onCollapse}
                className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
                title="Collapse panel"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
        
        <div className="flex border-t border-slate-200">
          <button
            onClick={() => setActiveTab('active')}
            className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'active'
                ? 'border-blue-600 text-blue-600 bg-blue-50'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            Active ({activeInputMeasurements.length + activeOutputMeasurements.length + activeTools.length + activeModels.length})
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'all'
                ? 'border-blue-600 text-blue-600 bg-blue-50'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            All ({allInputMeasurements.length + allOutputMeasurements.length + allTools.length + allModels.length})
          </button>
        </div>
      </div>
      
      {/* Data Object Lists */}
      <div className="flex-1 overflow-auto">
        {renderDataObjectSection('Input Measurements', inputMeasurements, 'input-measurements', 'text-blue-600', DatabaseIcon)}
        {renderDataObjectSection('Output Measurements', outputMeasurements, 'output-measurements', 'text-blue-600', DatabaseIcon)}
        {renderDataObjectSection('Tools', tools, 'tools', 'text-purple-600', ToolIcon)}
        {renderDataObjectSection('Models', models, 'models', 'text-green-600', BoxIcon)}
      </div>
    </div>
  );
}