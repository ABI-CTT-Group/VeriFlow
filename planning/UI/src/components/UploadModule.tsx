import { useState, useRef, useEffect } from 'react';
import { Upload, File, X, ChevronDown, ChevronRight, ChevronLeft } from 'lucide-react';
import { ResizablePanel } from './ResizablePanel';

interface UploadModuleProps {
  onPdfUpload?: (pdfUrl: string) => void;
  isHorizontallyCollapsed?: boolean;
  onToggleHorizontalCollapse?: () => void;
  onCollapseLeftPanel?: () => void;
  hasUploadedFiles?: boolean;
}

export function UploadModule({ onPdfUpload, isHorizontallyCollapsed, onToggleHorizontalCollapse, onCollapseLeftPanel, hasUploadedFiles }: UploadModuleProps) {
  const [files, setFiles] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Start collapsed if files have already been uploaded
  const [isExpanded, setIsExpanded] = useState(!hasUploadedFiles);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    // Mock file handling - in real implementation would handle actual files
    const mockPdf = 'breast_cancer_segmentation.pdf';
    const newFiles = [...files, mockPdf];
    setFiles(newFiles);
    onPdfUpload?.(mockPdf);
    // Auto-collapse after PDF upload
    setIsExpanded(false);
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = e.target.files;
    if (uploadedFiles && uploadedFiles.length > 0) {
      const fileNames = Array.from(uploadedFiles).map(f => f.name);
      const newFiles = [...files, ...fileNames];
      setFiles(newFiles);
      
      // Find and notify about PDF
      const pdfFile = fileNames.find(f => f.toLowerCase().endsWith('.pdf'));
      if (pdfFile && onPdfUpload) {
        onPdfUpload(pdfFile);
      }
      
      // Auto-collapse after file upload
      setIsExpanded(false);
    }
  };

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    
    // Update PDF if removed
    const pdfFile = newFiles.find(f => f.endsWith('.pdf'));
    if (onPdfUpload) {
      onPdfUpload(pdfFile || '');
    }
  };

  return (
    <div className="border-b border-slate-200 bg-white flex-shrink-0">
      <div className="flex items-center">
        {onCollapseLeftPanel && (
          <button
            onClick={onCollapseLeftPanel}
            className="px-2 py-3 text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors border-r border-slate-200"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`flex-1 flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors ${
            isExpanded ? 'border-b border-slate-200' : ''
          }`}
        >
          <div className="flex items-center gap-2 flex-1">
            <div className="text-left">
              <span className="text-sm font-medium text-slate-700">1. Upload Publication</span>
              <p className="text-xs text-slate-400">
                {files.length > 0 ? `${files.length} file${files.length > 1 ? 's' : ''} uploaded` : 'Upload a scientific paper (PDF)'}
              </p>
            </div>
          </div>
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
        </button>
      </div>
      {isExpanded && (
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
              Drop files here or <span className="text-blue-600 cursor-pointer" onClick={handleBrowseClick}>browse</span>
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
          
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileInput}
            className="hidden"
          />
        </div>
      )}
    </div>
  );
}