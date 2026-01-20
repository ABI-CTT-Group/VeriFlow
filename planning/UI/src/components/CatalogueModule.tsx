import { useState } from 'react';
import { ResizablePanel } from './ResizablePanel';
import { Database, Beaker, Box, ChevronDown, ChevronRight } from 'lucide-react';
import { useDrag } from 'react-dnd';

interface CatalogueItem {
  id: string;
  name: string;
  description: string;
  type: 'measurement' | 'tool' | 'model';
}

const catalogueData: CatalogueItem[] = [
  {
    id: 'meas-1',
    name: 'DCE-MRI Scans',
    description: 'T1-weighted breast MRI images from multicenter dataset',
    type: 'measurement'
  },
  {
    id: 'meas-2',
    name: 'Tumor Segmentation Masks',
    description: 'Ground truth segmentation annotations',
    type: 'measurement'
  },
  {
    id: 'tool-1',
    name: 'nnU-Net',
    description: 'Self-configuring deep learning segmentation framework',
    type: 'tool'
  },
  {
    id: 'tool-2',
    name: 'DICOM to NIfTI Converter',
    description: 'Format conversion adapter tool',
    type: 'tool'
  },
  {
    id: 'model-1',
    name: 'nnU-Net Pretrained Weights',
    description: 'Pre-trained model weights for breast tumor segmentation',
    type: 'model'
  }
];

function CatalogueItemCard({ item }: { item: CatalogueItem }) {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: item.type,
    item: { id: item.id, name: item.name, catalogueType: item.type },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));

  const getIcon = () => {
    switch (item.type) {
      case 'measurement':
        return <Database className="w-4 h-4" />;
      case 'tool':
        return <Beaker className="w-4 h-4" />;
      case 'model':
        return <Box className="w-4 h-4" />;
    }
  };

  return (
    <div
      ref={drag}
      className={`p-3 bg-white border border-slate-200 rounded cursor-move hover:shadow-md transition-shadow ${
        isDragging ? 'opacity-50' : ''
      }`}
    >
      <div className="flex items-start gap-2">
        <div className="mt-0.5 text-slate-500">{getIcon()}</div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-900 truncate">{item.name}</p>
          <p className="text-xs text-slate-500 mt-1">{item.description}</p>
        </div>
      </div>
    </div>
  );
}

function CatalogueSection({ 
  title, 
  type, 
  items 
}: { 
  title: string; 
  type: string; 
  items: CatalogueItem[] 
}) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="border-b border-slate-200 last:border-b-0">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 hover:bg-slate-50 transition-colors"
      >
        <span className="text-sm font-medium text-slate-700">{title}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">{items.length}</span>
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </button>
      {isExpanded && (
        <div className="p-3 space-y-2 bg-slate-50">
          {items.map((item) => (
            <CatalogueItemCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

export function CatalogueModule() {
  const measurements = catalogueData.filter(item => item.type === 'measurement');
  const tools = catalogueData.filter(item => item.type === 'tool');
  const models = catalogueData.filter(item => item.type === 'model');

  return (
    <ResizablePanel title="Catalogue" defaultHeight={400}>
      <div className="flex flex-col h-full">
        <CatalogueSection title="Measurements" type="measurement" items={measurements} />
        <CatalogueSection title="Tools" type="tool" items={tools} />
        <CatalogueSection title="Models" type="model" items={models} />
      </div>
    </ResizablePanel>
  );
}
