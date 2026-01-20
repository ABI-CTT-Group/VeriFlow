import { useState } from 'react';
import { Upload, File, X } from 'lucide-react';
import { ResizablePanel } from './ResizablePanel';

export function UploadModule() {
  const [files, setFiles] = useState<string[]>([
    'breast_cancer_segmentation.pdf',
    'supplementary_data.zip'
  ]);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    // Mock file handling
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  return (
    <ResizablePanel title="Upload" defaultHeight={200}>
      <div className="p-4 space-y-4">
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <Upload className="w-8 h-8 mx-auto text-slate-400 mb-2" />
          <p className="text-sm text-slate-600">
            Drop files here or <span className="text-blue-600 cursor-pointer">browse</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">PDF, ZIP, or code repositories</p>
        </div>

        {files.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-slate-500">Uploaded Files</p>
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-200"
              >
                <div className="flex items-center gap-2">
                  <File className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-700">{file}</span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </ResizablePanel>
  );
}
