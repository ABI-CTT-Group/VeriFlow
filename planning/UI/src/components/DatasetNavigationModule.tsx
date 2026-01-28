import { useState, useEffect } from 'react';
import { ResizablePanel } from './ResizablePanel';
import { Folder, FolderOpen, File, ChevronRight, ChevronDown, Eye, Edit, Image, Download } from 'lucide-react';

interface FileNode {
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  extension?: string;
}

interface DatasetNavigationModuleProps {
  selectedNode?: any;
  defaultViewerPlugin?: string;
  selectedDatasetId?: string | null;
}

// Map dataset IDs to their display names
const datasetNameMap: Record<string, string> = {
  'dce-mri-scans': 'DCE-MRI-Scans',
  'tumor-segmentation': 'Tumor-Segmentation'
};

// Generate file tree based on selected node or dataset
const generateFileTree = (selectedNode: any, selectedDatasetId?: string | null): FileNode[] => {
  // If a specific dataset is selected, use its name
  if (selectedDatasetId && datasetNameMap[selectedDatasetId]) {
    const datasetName = datasetNameMap[selectedDatasetId];
    
    return [{
      name: datasetName,
      type: 'folder',
      children: [
        { name: 'dataset_description.json', type: 'file', extension: 'json' },
        { name: 'subjects.tsv', type: 'file', extension: 'tsv' },
        {
          name: 'primary',
          type: 'folder',
          children: [
            {
              name: 'Subject_001',
              type: 'folder',
              children: [
                { name: 'T1w.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'metadata.json', type: 'file', extension: 'json' }
              ]
            },
            {
              name: 'Subject_002',
              type: 'folder',
              children: [
                { name: 'T1w.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'metadata.json', type: 'file', extension: 'json' }
              ]
            }
          ]
        },
        { name: 'code', type: 'folder', children: [] }
      ]
    }];
  }
  
  if (!selectedNode) {
    return [{
      name: 'No-Data-Object-Selected',
      type: 'folder',
      children: []
    }];
  }

  const nodeName = selectedNode.name?.replace(/\s+/g, '-') || 'Data-Object';
  
  // Generate different SDS structures based on node type
  if (selectedNode.type === 'measurement' && selectedNode.role === 'input') {
    return [{
      name: nodeName,
      type: 'folder',
      children: [
        { name: 'dataset_description.json', type: 'file', extension: 'json' },
        { name: 'subjects.tsv', type: 'file', extension: 'tsv' },
        {
          name: 'primary',
          type: 'folder',
          children: [
            {
              name: 'Subject_001',
              type: 'folder',
              children: [
                { name: 'T1w.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'metadata.json', type: 'file', extension: 'json' }
              ]
            },
            {
              name: 'Subject_002',
              type: 'folder',
              children: [
                { name: 'T1w.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'metadata.json', type: 'file', extension: 'json' }
              ]
            }
          ]
        },
        {
          name: 'code',
          type: 'folder',
          children: [
            { name: 'preprocessing.cwl', type: 'file', extension: 'cwl' },
            { name: 'README.md', type: 'file', extension: 'md' }
          ]
        }
      ]
    }];
  } else if (selectedNode.type === 'tool') {
    return [{
      name: nodeName,
      type: 'folder',
      children: [
        { name: 'dataset_description.json', type: 'file', extension: 'json' },
        {
          name: 'code',
          type: 'folder',
          children: [
            { name: 'workflow.cwl', type: 'file', extension: 'cwl' },
            { name: 'Dockerfile', type: 'file', extension: 'docker' },
            { name: 'requirements.txt', type: 'file', extension: 'txt' }
          ]
        },
        {
          name: 'derivative',
          type: 'folder',
          children: [
            {
              name: 'Subject_001',
              type: 'folder',
              children: [
                { name: 'output.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'log.txt', type: 'file', extension: 'txt' }
              ]
            }
          ]
        }
      ]
    }];
  } else if (selectedNode.type === 'model') {
    return [{
      name: nodeName,
      type: 'folder',
      children: [
        { name: 'dataset_description.json', type: 'file', extension: 'json' },
        { name: 'model_description.json', type: 'file', extension: 'json' },
        {
          name: 'primary',
          type: 'folder',
          children: [
            { name: 'weights.pth', type: 'file', extension: 'pth' },
            { name: 'architecture.json', type: 'file', extension: 'json' },
            { name: 'training_config.yaml', type: 'file', extension: 'yaml' }
          ]
        },
        {
          name: 'docs',
          type: 'folder',
          children: [
            { name: 'README.md', type: 'file', extension: 'md' },
            { name: 'training_log.txt', type: 'file', extension: 'txt' }
          ]
        }
      ]
    }];
  } else if (selectedNode.type === 'measurement' && selectedNode.role === 'output') {
    return [{
      name: nodeName,
      type: 'folder',
      children: [
        { name: 'dataset_description.json', type: 'file', extension: 'json' },
        { name: 'subjects.tsv', type: 'file', extension: 'tsv' },
        {
          name: 'derivative',
          type: 'folder',
          children: [
            {
              name: 'Subject_001',
              type: 'folder',
              children: [
                { name: 'tumor_mask.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'metrics.json', type: 'file', extension: 'json' }
              ]
            },
            {
              name: 'Subject_002',
              type: 'folder',
              children: [
                { name: 'tumor_mask.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'metrics.json', type: 'file', extension: 'json' }
              ]
            }
          ]
        }
      ]
    }];
  }

  // Default structure
  return [{
    name: nodeName,
    type: 'folder',
    children: [
      { name: 'dataset_description.json', type: 'file', extension: 'json' },
      { name: 'README.md', type: 'file', extension: 'md' }
    ]
  }];
};

function FileTreeNode({ node, depth = 0, onFileClick }: { node: FileNode; depth?: number; onFileClick?: (node: FileNode) => void }) {
  const [isExpanded, setIsExpanded] = useState(depth < 2);

  if (node.type === 'file') {
    return (
      <div
        className="flex items-center gap-2 px-2 py-1 hover:bg-slate-100 cursor-pointer rounded"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => onFileClick?.(node)}
      >
        <File className="w-4 h-4 text-slate-400" />
        <span className="text-sm text-slate-700">{node.name}</span>
      </div>
    );
  }

  return (
    <div>
      <div
        className="flex items-center gap-2 px-2 py-1 hover:bg-slate-100 cursor-pointer rounded"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-400" />
        )}
        {isExpanded ? (
          <FolderOpen className="w-4 h-4 text-blue-500" />
        ) : (
          <Folder className="w-4 h-4 text-blue-500" />
        )}
        <span className="text-sm text-slate-700 font-medium">{node.name}</span>
      </div>
      {isExpanded && node.children && (
        <div>
          {node.children.map((child, index) => (
            <FileTreeNode key={index} node={child} depth={depth + 1} onFileClick={onFileClick} />
          ))}
        </div>
      )}
    </div>
  );
}

export function DatasetNavigationModule({ selectedNode, defaultViewerPlugin, selectedDatasetId }: DatasetNavigationModuleProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['DCE-MRI-Scans', 'Tumor-Segmentation', 'primary']));
  const [viewerMode, setViewerMode] = useState<'view' | 'edit'>('view');

  const determineViewer = (fileExtension?: string): string | null => {
    if (defaultViewerPlugin !== 'auto') {
      return defaultViewerPlugin;
    }
    
    // Auto-detect based on file extension
    if (fileExtension === 'nii.gz' || fileExtension === 'nii') {
      return 'volview';
    } else if (fileExtension === 'json' || fileExtension === 'cwl' || fileExtension === 'txt' || fileExtension === 'md' || fileExtension === 'yaml' || fileExtension === 'docker') {
      return 'editor';
    } else if (fileExtension === 'png' || fileExtension === 'jpg' || fileExtension === 'jpeg') {
      return 'image';
    }
    return null;
  };

  const handleFileClick = (node: FileNode) => {
    setSelectedFile(node.name);
  };

  const plugins = [
    { id: 'volview', name: 'VolView', icon: Eye, description: '3D Medical Image Viewer' },
    { id: 'editor', name: 'Code Editor', icon: Edit, description: 'Syntax-highlighted editor' },
    { id: 'image', name: 'Image Viewer', icon: Image, description: 'Image preview' }
  ];

  const fileTree = generateFileTree(selectedNode, selectedDatasetId);
  const activePlugin = selectedFile ? determineViewer(fileTree.find(node => node.name === selectedFile)?.extension) : null;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <ResizablePanel title="Dataset Navigation" defaultHeight={400}>
        <div className="p-2">
          {fileTree.map((node, index) => (
            <FileTreeNode key={index} node={node} onFileClick={handleFileClick} />
          ))}
        </div>
      </ResizablePanel>

      <ResizablePanel title="File View" defaultHeight={300}>
        <div className="p-4">
          {activePlugin ? (
            <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {activePlugin === 'volview' && <Eye className="w-5 h-5 text-blue-600" />}
                  {activePlugin === 'editor' && <Edit className="w-5 h-5 text-blue-600" />}
                  {activePlugin === 'image' && <Image className="w-5 h-5 text-blue-600" />}
                  <div>
                    <span className="text-sm font-medium text-slate-900">
                      {plugins.find(p => p.id === activePlugin)?.name}
                    </span>
                    {selectedFile && (
                      <p className="text-xs text-slate-500">{selectedFile}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => {
                    setSelectedFile(null);
                  }}
                  className="text-xs text-slate-500 hover:text-slate-700"
                >
                  Close
                </button>
              </div>
              <div className="bg-slate-900 rounded aspect-video flex items-center justify-center">
                <p className="text-slate-400 text-sm">
                  {activePlugin === 'volview' && '3D Visualization Placeholder'}
                  {activePlugin === 'editor' && 'Code Editor Placeholder'}
                  {activePlugin === 'image' && 'Image Preview Placeholder'}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-400">
              <div className="text-center">
                <Eye className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No file selected</p>
                <p className="text-xs mt-1">Click on a file in the tree above to view it</p>
              </div>
            </div>
          )}
        </div>
      </ResizablePanel>

      {/* Export Section */}
      <div className="border-t border-slate-200 p-3 flex-shrink-0 bg-white">
        <div className="space-y-2">
          <button 
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export Selected Data Object
          </button>
          <button className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-slate-300 text-slate-700 text-sm rounded hover:bg-slate-50 transition-colors">
            <Download className="w-4 h-4" />
            Export All Data Objects
          </button>
          <p className="text-xs text-slate-400 text-center mt-2">
            Exports are packaged in SDS format
          </p>
        </div>
      </div>
    </div>
  );
}