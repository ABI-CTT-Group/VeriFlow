import { FileText, X } from 'lucide-react';
import { useState } from 'react';

interface Annotation {
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  propertyId: string;
  label: string;
}

interface ViewerPanelProps {
  pdfUrl?: string;
  annotations?: Annotation[];
  onClose?: () => void;
  activePropertyId?: string;
}

export function ViewerPanel({ pdfUrl, annotations, onClose, activePropertyId }: ViewerPanelProps) {
  const [currentPage, setCurrentPage] = useState(1);
  
  // Define annotations for different extracted properties
  const extractionAnnotations: Annotation[] = [
    // Page 1 - Title
    { page: 1, x: 10, y: 15, width: 80, height: 8, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'paper-title', label: 'Paper Title' },
    // Page 1 - Authors
    { page: 1, x: 10, y: 28, width: 60, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'paper-authors', label: 'Authors' },
    // Page 1 - Year
    { page: 1, x: 10, y: 38, width: 20, height: 4, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'paper-year', label: 'Year' },
    // Page 1 - Abstract
    { page: 1, x: 10, y: 50, width: 80, height: 20, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'paper-abstract', label: 'Abstract' },
    // Page 2 - Investigation info
    { page: 2, x: 10, y: 20, width: 80, height: 15, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'inv-title', label: 'Investigation Title' },
    { page: 2, x: 10, y: 38, width: 80, height: 18, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'inv-description', label: 'Investigation Description' },
    { page: 2, x: 10, y: 60, width: 30, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'inv-date', label: 'Study Date' },
    // Page 3 - Study info
    { page: 3, x: 10, y: 25, width: 70, height: 8, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'study-title', label: 'Study Title' },
    { page: 3, x: 10, y: 38, width: 80, height: 12, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'study-description', label: 'Study Description' },
    { page: 3, x: 10, y: 55, width: 35, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'study-subjects', label: 'Number of Subjects' },
    { page: 3, x: 10, y: 65, width: 40, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'study-design', label: 'Study Design' },
    // Page 4 - Assay info
    { page: 4, x: 10, y: 30, width: 50, height: 8, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'assay-name', label: 'Assay Name' },
    // Workflow Steps - Page 4
    { page: 4, x: 10, y: 55, width: 65, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'step-step-1', label: 'Step 1: Data Acquisition' },
    { page: 4, x: 10, y: 65, width: 70, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'step-step-2', label: 'Step 2: DICOM to NIfTI' },
    { page: 4, x: 10, y: 75, width: 68, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'step-step-3', label: 'Step 3: Normalization' },
    { page: 4, x: 10, y: 85, width: 72, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'step-step-4', label: 'Step 4: Model Training' },
  ];

  const getHighlightedSection = (propertyId?: string) => {
    const sections: Record<string, { title: string; content: string; location: string }> = {
      'paper-title': {
        title: 'Paper Title',
        content: 'Breast Cancer Segmentation Using Deep Learning',
        location: 'Page 1, Title Section'
      },
      'paper-authors': {
        title: 'Authors',
        content: 'Smith, J., Johnson, A., Williams, B., Brown, C.',
        location: 'Page 1, Authors Section'
      },
      'paper-year': {
        title: 'Publication Year',
        content: '2023',
        location: 'Page 1, Header'
      },
      'paper-abstract': {
        title: 'Abstract',
        content: 'This study presents a novel approach to automated breast cancer segmentation...',
        location: 'Page 1, Abstract'
      },
      'inv-title': {
        title: 'Investigation Title',
        content: 'Automated Tumor Detection Investigation',
        location: 'Page 2, Introduction'
      },
      'inv-description': {
        title: 'Investigation Description',
        content: 'Investigation of automated deep learning methods for breast tumor detection and segmentation in DCE-MRI images',
        location: 'Page 2, Methods'
      },
      'inv-date': {
        title: 'Study Date',
        content: 'January 2023',
        location: 'Page 2, Timeline'
      },
      'study-title': {
        title: 'Study Title',
        content: 'MRI-based Segmentation Study',
        location: 'Page 3, Study Design'
      },
      'study-description': {
        title: 'Study Description',
        content: 'Comprehensive study of U-Net based segmentation on breast MRI scans',
        location: 'Page 3, Methods'
      },
      'study-subjects': {
        title: 'Number of Subjects',
        content: '384 subjects',
        location: 'Page 3, Participants'
      },
      'study-design': {
        title: 'Study Design',
        content: 'Retrospective cohort study',
        location: 'Page 3, Study Design'
      },
      'assay-name': {
        title: 'Assay Name',
        content: 'U-Net Training Assay',
        location: 'Page 4, Training Protocol'
      },
      'step-step-1': {
        title: 'Step 1: Data Acquisition',
        content: 'Acquisition of DCE-MRI scans from 384 subjects',
        location: 'Page 4, Workflow'
      },
      'step-step-2': {
        title: 'Step 2: DICOM to NIfTI',
        content: 'Conversion of DICOM images to NIfTI format',
        location: 'Page 4, Workflow'
      },
      'step-step-3': {
        title: 'Step 3: Normalization',
        content: 'Intensity normalization and bias field correction',
        location: 'Page 4, Workflow'
      },
      'step-step-4': {
        title: 'Step 4: Model Training',
        content: 'Training of U-Net model with data augmentation',
        location: 'Page 4, Workflow'
      }
    };

    return sections[propertyId || ''] || null;
  };

  const highlightedSection = getHighlightedSection(activePropertyId);

  // Get active annotation for current property
  const activeAnnotation = extractionAnnotations.find(a => a.propertyId === activePropertyId);
  
  // Auto-navigate to the page containing the active annotation
  if (activeAnnotation && currentPage !== activeAnnotation.page) {
    setCurrentPage(activeAnnotation.page);
  }

  if (!pdfUrl) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50">
        <div className="text-center text-slate-400">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">No document selected</p>
          <p className="text-xs mt-1">Click "Source" on any property to view</p>
        </div>
      </div>
    );
  }

  const renderPDFPage = (pageNum: number) => {
    // Get annotations for this page
    const pageAnnotations = extractionAnnotations.filter(a => a.page === pageNum);
    const activePageAnnotation = activeAnnotation?.page === pageNum ? activeAnnotation : null;

    return (
      <div className="relative bg-white border border-slate-300 mx-auto" style={{ width: '612px', height: '792px' }}>
        {/* Mock PDF Content */}
        <div className="p-12 text-sm leading-relaxed text-slate-700">
          {pageNum === 1 && (
            <>
              <div className="relative">
                <h1 className="text-3xl font-bold mb-6 text-slate-900">
                  Breast Cancer Segmentation Using Deep Learning
                </h1>
              </div>
              
              <div className="relative mt-4">
                <p className="text-base text-slate-600 mb-2">
                  Smith, J., Johnson, A., Williams, B., Brown, C.
                </p>
                <p className="text-sm text-slate-500">Department of Medical Imaging, University Hospital</p>
              </div>

              <div className="relative mt-4">
                <p className="text-sm text-slate-600">Published: 2023</p>
              </div>

              <div className="relative mt-8">
                <h2 className="text-xl font-bold mb-3 text-slate-900">Abstract</h2>
                <p className="text-justify">
                  This study presents a novel approach to automated breast cancer segmentation
                  using deep learning techniques on DCE-MRI scans. Early detection and accurate 
                  segmentation of tumors in medical imaging is crucial for effective treatment 
                  planning. We developed and validated a U-Net based model trained on 384 subjects
                  from the MAMA-MIA dataset, achieving state-of-the-art segmentation performance.
                </p>
              </div>
            </>
          )}

          {pageNum === 2 && (
            <>
              <h2 className="text-xl font-bold mb-4 text-slate-900">Introduction</h2>
              
              <div className="relative">
                <p className="mb-4 text-justify">
                  This investigation focuses on automated tumor detection using deep learning methods.
                  The primary objective is to develop a reliable system for breast tumor detection 
                  and segmentation in DCE-MRI images. The automated approach aims to reduce manual 
                  effort while improving consistency and accuracy in tumor identification.
                </p>
              </div>

              <div className="relative mt-6">
                <p className="mb-4 text-justify">
                  Investigation of automated deep learning methods for breast tumor detection and 
                  segmentation in DCE-MRI images represents a critical advancement in medical imaging 
                  analysis. Our approach leverages state-of-the-art convolutional neural networks to
                  achieve robust segmentation across diverse patient populations.
                </p>
              </div>

              <div className="relative mt-4">
                <p className="text-sm text-slate-600">Study Timeline: January 2023 - June 2023</p>
              </div>
            </>
          )}

          {pageNum === 3 && (
            <>
              <h2 className="text-xl font-bold mb-4 text-slate-900">Methods</h2>
              
              <div className="relative mb-6">
                <h3 className="text-lg font-semibold mb-2 text-slate-800">MRI-based Segmentation Study</h3>
                <p className="text-justify">
                  We conducted a comprehensive study of U-Net based segmentation on breast MRI scans.
                  The methodology involved multiple stages of image processing, data augmentation,
                  and model training to ensure robust performance across varied imaging conditions.
                </p>
              </div>

              <div className="relative mb-6">
                <h3 className="text-base font-semibold mb-2 text-slate-800">Participants</h3>
                <p className="text-justify">
                  We collected DCE-MRI scans from 384 subjects diagnosed with breast cancer.
                  All images were acquired using a 3T MRI scanner with standardized T1-weighted 
                  sequences following institutional protocols.
                </p>
              </div>

              <div className="relative">
                <h3 className="text-base font-semibold mb-2 text-slate-800">Study Design</h3>
                <p className="text-justify">
                  This retrospective cohort study analyzed existing medical imaging data collected
                  between 2020 and 2023 from multiple clinical sites.
                </p>
              </div>
            </>
          )}

          {pageNum === 4 && (
            <>
              <h2 className="text-xl font-bold mb-4 text-slate-900">Training Protocol</h2>
              
              <div className="relative mb-6">
                <h3 className="text-lg font-semibold mb-2 text-slate-800">U-Net Training Assay</h3>
                <p className="text-justify mb-4">
                  The segmentation model was trained using a U-Net architecture with pretrained 
                  nnU-Net weights. The training protocol included data augmentation techniques such 
                  as random rotations, elastic deformations, and intensity variations.
                </p>
                <p className="text-justify">
                  Model optimization was performed using the Adam optimizer with a learning rate 
                  of 0.001, batch size of 16, and training for 200 epochs with early stopping based 
                  on validation performance.
                </p>
              </div>

              <h3 className="text-base font-semibold mb-2 text-slate-800">Data Processing</h3>
              <p className="text-justify">
                DICOM images were converted to NIfTI format using the dcm2niix tool.
                Preprocessing steps included intensity normalization using Z-score standardization
                and bias field correction using the N4ITK algorithm.
              </p>
            </>
          )}
        </div>

        {/* Annotation Overlays */}
        {pageAnnotations.map((annotation, idx) => {
          const isActive = annotation.propertyId === activePropertyId;
          return (
            <div
              key={idx}
              className={`absolute pointer-events-none transition-all duration-300 ${
                isActive ? 'opacity-100 ring-2 ring-blue-500' : 'opacity-0'
              }`}
              style={{
                left: `${annotation.x}%`,
                top: `${annotation.y}%`,
                width: `${annotation.width}%`,
                height: `${annotation.height}%`,
                backgroundColor: annotation.color,
                borderLeft: isActive ? '4px solid #3b82f6' : 'none',
              }}
            >
              {isActive && (
                <div className="absolute -top-6 left-0 bg-blue-600 text-white text-xs px-2 py-1 rounded whitespace-nowrap shadow-lg">
                  {annotation.label}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-slate-600" />
          <div>
            <span className="text-sm font-medium text-slate-700">Document Viewer</span>
            {highlightedSection && (
              <p className="text-xs text-slate-500">{highlightedSection.location}</p>
            )}
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Extraction Info Banner */}
      {highlightedSection && (
        <div className="px-4 py-2 bg-blue-50 border-b border-blue-200 flex-shrink-0">
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-blue-900">Scholar extracted from {highlightedSection.location}:</p>
              <p className="text-xs text-blue-700 mt-0.5 italic">"{highlightedSection.content}"</p>
            </div>
          </div>
        </div>
      )}

      {/* PDF Viewer Area */}
      <div className="flex-1 overflow-auto bg-slate-100 p-6">
        {renderPDFPage(currentPage)}
      </div>

      {/* Page Navigation */}
      <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between flex-shrink-0 bg-white">
        <button
          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="px-3 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <span className="text-xs text-slate-600">
          Page {currentPage} of 4
        </span>
        <button
          onClick={() => setCurrentPage(Math.min(4, currentPage + 1))}
          disabled={currentPage === 4}
          className="px-3 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  );
}