import { useState } from 'react';
import { ResizablePanel } from './ResizablePanel';
import { Folder, FolderOpen, File, ChevronRight, ChevronDown, Eye, Edit, Image } from 'lucide-react';

interface FileNode {
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  extension?: string;
}

const fileTree: FileNode[] = [
  {
    name: 'MAMA-MIA-Dataset',
    type: 'folder',
    children: [
      {
        name: 'dataset_description.json',
        type: 'file',
        extension: 'json'
      },
      {
        name: 'subjects.tsv',
        type: 'file',
        extension: 'tsv'
      },
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
        name: 'derivative',
        type: 'folder',
        children: [
          {
            name: 'Subject_001',
            type: 'folder',
            children: [
              { name: 'tumor_mask.nii.gz', type: 'file', extension: 'nii.gz' }
            ]
          }
        ]
      },
      {
        name: 'code',
        type: 'folder',
        children: [
          { name: 'workflow.cwl', type: 'file', extension: 'cwl' },
          { name: 'Dockerfile', type: 'file', extension: 'docker' }
        ]
      }
    ]
  }
];

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

export function DatasetNavigationModule() {
  const [activePlugin, setActivePlugin] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);

  const handleFileClick = (node: FileNode) => {
    setSelectedFile(node);
    // Auto-open appropriate plugin based on file type
    if (node.extension === 'nii.gz') {
      setActivePlugin('volview');
    } else if (node.extension === 'json' || node.extension === 'cwl') {
      setActivePlugin('editor');
    }
  };

  const plugins = [
    { id: 'volview', name: 'VolView', icon: Eye, description: '3D Medical Image Viewer' },
    { id: 'editor', name: 'Code Editor', icon: Edit, description: 'Syntax-highlighted editor' },
    { id: 'image', name: 'Image Viewer', icon: Image, description: 'Image preview' }
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <ResizablePanel title="Dataset Navigation" defaultHeight={400}>
        <div className="p-2">
          {fileTree.map((node, index) => (
            <FileTreeNode key={index} node={node} onFileClick={handleFileClick} />
          ))}
        </div>
      </ResizablePanel>

      <ResizablePanel title="Plugins" defaultHeight={300}>
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
                      <p className="text-xs text-slate-500">{selectedFile.name}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => {
                    setActivePlugin(null);
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
            <div className="space-y-2">
              <p className="text-xs text-slate-500 mb-3">Available Plugins</p>
              {plugins.map((plugin) => (
                <button
                  key={plugin.id}
                  onClick={() => setActivePlugin(plugin.id)}
                  className="w-full flex items-start gap-3 p-3 border border-slate-200 rounded hover:bg-slate-50 transition-colors text-left"
                >
                  <plugin.icon className="w-5 h-5 text-slate-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">{plugin.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{plugin.description}</p>
                  </div>
                </button>
              ))}
              <div className="pt-3 border-t border-slate-200 mt-4">
                <p className="text-xs text-slate-400 italic">
                  Click on files in the tree above to open with plugins
                </p>
              </div>
            </div>
          )}
        </div>
      </ResizablePanel>
    </div>
  );
}