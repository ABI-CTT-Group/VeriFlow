import { useState } from 'react';
import { Settings, Download, X, Plus, Trash2 } from 'lucide-react';

interface ConfigurationPanelProps {
  defaultViewerPlugin?: string;
  onViewerPluginChange?: (plugin: string) => void;
}

export function ConfigurationPanel({ defaultViewerPlugin = 'auto', onViewerPluginChange }: ConfigurationPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'general' | 'plugins'>('general');
  const [reanalysisMode, setReanalysisMode] = useState<'manual' | 'auto'>('manual');
  const [saveIntermediateResults, setSaveIntermediateResults] = useState(false);
  const [plugins, setPlugins] = useState([
    { id: '1', name: 'BIDS Validator', version: '1.2.0', enabled: true },
    { id: '2', name: 'SPARC Exporter', version: '2.0.1', enabled: true },
    { id: '3', name: 'CWL Generator', version: '1.5.0', enabled: false }
  ]);

  const togglePlugin = (id: string) => {
    setPlugins(plugins.map(p => p.id === id ? { ...p, enabled: !p.enabled } : p));
  };

  const removePlugin = (id: string) => {
    setPlugins(plugins.filter(p => p.id !== id));
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50"
      >
        <Settings className="w-4 h-4" />
        Configuration
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 w-96 bg-white border border-slate-200 rounded-lg shadow-xl z-50">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="font-medium text-slate-900">Configuration</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-200">
              <button
                onClick={() => setActiveTab('general')}
                className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'general'
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                General
              </button>
              <button
                onClick={() => setActiveTab('plugins')}
                className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'plugins'
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                Plugins
              </button>
            </div>

            <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
              {activeTab === 'general' ? (
                <>
                  {/* Re-analysis Mode */}
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-2">
                      Scholar Re-analysis Mode
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="reanalysis"
                          value="manual"
                          checked={reanalysisMode === 'manual'}
                          onChange={(e) => setReanalysisMode(e.target.value as 'manual')}
                          className="text-blue-600"
                        />
                        <div>
                          <p className="text-sm text-slate-900">Manual</p>
                          <p className="text-xs text-slate-500">
                            Re-analyze only when button is pressed
                          </p>
                        </div>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="reanalysis"
                          value="auto"
                          checked={reanalysisMode === 'auto'}
                          onChange={(e) => setReanalysisMode(e.target.value as 'auto')}
                          className="text-blue-600"
                        />
                        <div>
                          <p className="text-sm text-slate-900">Automatic</p>
                          <p className="text-xs text-slate-500">
                            Re-analyze after each property edit
                          </p>
                        </div>
                      </label>
                    </div>
                  </div>

                  {/* Workflow Options */}
                  <div className="pt-3 border-t border-slate-200">
                    <label className="text-sm font-medium text-slate-700 block mb-2">
                      Workflow Execution
                    </label>
                    <label className="flex items-start gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={saveIntermediateResults}
                        onChange={(e) => setSaveIntermediateResults(e.target.checked)}
                        className="mt-1 text-blue-600"
                      />
                      <div>
                        <p className="text-sm text-slate-900">Save Intermediate Results</p>
                        <p className="text-xs text-slate-500">
                          Serialize transient outputs as SDS datasets
                        </p>
                      </div>
                    </label>
                  </div>

                  {/* Default File Viewer */}
                  <div className="pt-3 border-t border-slate-200">
                    <label className="text-sm font-medium text-slate-700 block mb-2">
                      Default File Viewer
                    </label>
                    <select
                      value={defaultViewerPlugin}
                      onChange={(e) => onViewerPluginChange?.(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="auto">Auto-detect (based on file type)</option>
                      <option value="volview">VolView (3D Medical Imaging)</option>
                      <option value="editor">Code Editor</option>
                      <option value="image">Image Viewer</option>
                    </select>
                    <p className="text-xs text-slate-500 mt-1">
                      Plugin used when viewing files in Results panel
                    </p>
                  </div>

                  {/* Status */}
                  <div className="pt-3 border-t border-slate-200">
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-600">Active Agents</span>
                        <span className="text-slate-900 font-medium">3/3</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Airflow Status</span>
                        <span className="text-green-600 font-medium">Connected</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Current Phase</span>
                        <span className="text-slate-900 font-medium">Stage 2</span>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* Plugins Tab */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <label className="text-sm font-medium text-slate-700">
                        Registered Plugins
                      </label>
                      <button className="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                        <Plus className="w-3 h-3" />
                        Add Plugin
                      </button>
                    </div>
                    
                    <div className="space-y-2">
                      {plugins.map((plugin) => (
                        <div
                          key={plugin.id}
                          className="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg"
                        >
                          <input
                            type="checkbox"
                            checked={plugin.enabled}
                            onChange={() => togglePlugin(plugin.id)}
                            className="text-blue-600"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-900">{plugin.name}</p>
                            <p className="text-xs text-slate-500">v{plugin.version}</p>
                          </div>
                          <button
                            onClick={() => removePlugin(plugin.id)}
                            className="text-red-400 hover:text-red-600 p-1"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-200">
                    <p className="text-xs text-slate-500">
                      Plugins extend VeriFlow functionality. View plugin outputs in the Viewer panel.
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}