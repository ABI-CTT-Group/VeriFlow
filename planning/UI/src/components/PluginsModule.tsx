import { useState } from 'react';
import { ResizablePanel } from './ResizablePanel';
import { Puzzle, Eye, Edit, Image } from 'lucide-react';

export function PluginsModule() {
  const [activePlugin, setActivePlugin] = useState<string | null>(null);

  const plugins = [
    { id: 'volview', name: 'VolView', icon: Eye, description: '3D Medical Image Viewer' },
    { id: 'editor', name: 'Code Editor', icon: Edit, description: 'Syntax-highlighted editor' },
    { id: 'image', name: 'Image Viewer', icon: Image, description: 'Image preview' }
  ];

  return (
    <ResizablePanel title="Plugins" defaultHeight={200}>
      <div className="p-4">
        {activePlugin ? (
          <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-slate-900">VolView</span>
              </div>
              <button
                onClick={() => setActivePlugin(null)}
                className="text-xs text-slate-500 hover:text-slate-700"
              >
                Close
              </button>
            </div>
            <div className="bg-slate-900 rounded aspect-video flex items-center justify-center">
              <p className="text-slate-400 text-sm">3D Visualization Placeholder</p>
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
                Right-click files in Dataset Navigation to open with plugins
              </p>
            </div>
          </div>
        )}
      </div>
    </ResizablePanel>
  );
}
