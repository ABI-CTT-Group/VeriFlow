import { useState } from 'react';
import { Settings, Download, X } from 'lucide-react';

export function ConfigurationPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [reanalysisMode, setReanalysisMode] = useState<'manual' | 'auto'>('manual');
  const [saveIntermediateResults, setSaveIntermediateResults] = useState(false);

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
          <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-xl z-50">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="font-medium text-slate-900">Global Configuration</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-4">
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

              {/* Export Options */}
              <div className="pt-3 border-t border-slate-200">
                <label className="text-sm font-medium text-slate-700 block mb-3">
                  Export Options
                </label>
                <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                  <Download className="w-4 h-4" />
                  Export All SDS Datasets
                </button>
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
            </div>
          </div>
        </>
      )}
    </div>
  );
}
