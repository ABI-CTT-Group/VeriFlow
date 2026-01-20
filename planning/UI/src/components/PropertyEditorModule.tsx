import { ResizablePanel } from './ResizablePanel';
import { Save, Undo } from 'lucide-react';

interface PropertyEditorModuleProps {
  selectedNode: any;
}

export function PropertyEditorModule({ selectedNode }: PropertyEditorModuleProps) {
  if (!selectedNode) {
    return (
      <ResizablePanel title="Property Editor" defaultHeight={300}>
        <div className="p-4 text-center text-slate-400">
          <p className="text-sm">Select a node to edit its properties</p>
        </div>
      </ResizablePanel>
    );
  }

  return (
    <ResizablePanel title="Property Editor" defaultHeight={300}>
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div>
            <p className="text-sm font-medium text-slate-900">{selectedNode.name}</p>
            <p className="text-xs text-slate-500 mt-0.5">
              {selectedNode.type || 'Node'} Properties
            </p>
          </div>
          <div className="flex gap-1">
            <button className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded">
              <Undo className="w-4 h-4" />
            </button>
            <button className="p-1.5 text-blue-600 hover:bg-blue-50 rounded">
              <Save className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Properties */}
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-700 block mb-1">Name</label>
            <input
              type="text"
              defaultValue={selectedNode.name}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {selectedNode.description && (
            <div>
              <label className="text-xs font-medium text-slate-700 block mb-1">
                Description
              </label>
              <textarea
                defaultValue={selectedNode.description}
                rows={3}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {selectedNode.confidence !== undefined && (
            <div>
              <label className="text-xs font-medium text-slate-700 block mb-1">
                Confidence Score
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="100"
                  defaultValue={selectedNode.confidence * 100}
                  className="flex-1"
                />
                <span className="text-sm font-medium text-slate-900 w-12">
                  {(selectedNode.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          )}

          {selectedNode.status && (
            <div>
              <label className="text-xs font-medium text-slate-700 block mb-1">Status</label>
              <select
                defaultValue={selectedNode.status}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="pending">Pending</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="error">Error</option>
              </select>
            </div>
          )}

          {selectedNode.totalSubjects && (
            <div>
              <label className="text-xs font-medium text-slate-700 block mb-1">
                Total Subjects
              </label>
              <input
                type="number"
                defaultValue={selectedNode.totalSubjects}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {/* Metadata */}
          <div className="pt-3 border-t border-slate-200">
            <p className="text-xs font-medium text-slate-700 mb-2">Metadata</p>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600">Format</span>
                <span className="text-slate-900 font-mono">NIfTI (application/x-nifti)</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600">MIME Type</span>
                <span className="text-slate-900 font-mono">edam:format_3987</span>
              </div>
              {selectedNode.id && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-600">Node ID</span>
                  <span className="text-slate-900 font-mono">{selectedNode.id}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </ResizablePanel>
  );
}
