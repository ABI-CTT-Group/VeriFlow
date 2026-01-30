import { useState, useRef, useEffect } from 'react';
import { Send, Terminal, User, Bot } from 'lucide-react';
import { Resizable } from 're-resizable';

interface Message {
  id: string;
  type: 'user' | 'agent' | 'system';
  agent?: 'scholar' | 'engineer' | 'reviewer';
  content: string;
  timestamp: Date;
}

const initialMessages: Message[] = [
  {
    id: '1',
    type: 'system',
    content: 'VeriFlow initialized. Agents ready.',
    timestamp: new Date(Date.now() - 300000)
  },
  {
    id: '2',
    type: 'agent',
    agent: 'scholar',
    content: 'Analyzing PDF: breast_cancer_segmentation.pdf...',
    timestamp: new Date(Date.now() - 240000)
  },
  {
    id: '3',
    type: 'agent',
    agent: 'scholar',
    content: 'Extracted ISA hierarchy: 1 Investigation, 1 Study, 2 Assays. Creating SDS metadata...',
    timestamp: new Date(Date.now() - 180000)
  },
  {
    id: '4',
    type: 'agent',
    agent: 'scholar',
    content: 'Identified measurements: DCE-MRI Scans (384 subjects), Tools: nnU-Net, Models: Pretrained weights',
    timestamp: new Date(Date.now() - 120000)
  },
  {
    id: '5',
    type: 'agent',
    agent: 'reviewer',
    content: 'Validation complete. Study design populated. Ready for workflow assembly.',
    timestamp: new Date(Date.now() - 60000)
  }
];

export function ConsoleModule() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages([...messages, newMessage]);
    setInput('');

    // Simulate agent response
    setTimeout(() => {
      const response: Message = {
        id: (Date.now() + 1).toString(),
        type: 'agent',
        agent: 'reviewer',
        content: 'I understand your request. Processing...',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, response]);
    }, 1000);
  };

  const getAgentColor = (agent?: string) => {
    switch (agent) {
      case 'scholar':
        return 'text-blue-600';
      case 'engineer':
        return 'text-purple-600';
      case 'reviewer':
        return 'text-green-600';
      default:
        return 'text-slate-600';
    }
  };

  const getAgentName = (agent?: string) => {
    switch (agent) {
      case 'scholar':
        return 'Scholar Agent';
      case 'engineer':
        return 'Engineer Agent';
      case 'reviewer':
        return 'Reviewer Agent';
      default:
        return 'System';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-2 border-b border-slate-200 flex items-center justify-between bg-slate-50 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-slate-600" />
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-xs text-slate-500">All agents active</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
        {messages.map((message) => (
          <div key={message.id} className="flex gap-3">
            <span className="text-slate-400 whitespace-nowrap">
              {formatTime(message.timestamp)}
            </span>
            <div className="flex-1">
              {message.type === 'user' ? (
                <div className="flex items-start gap-2">
                  <User className="w-4 h-4 text-slate-600 mt-0.5" />
                  <span className="text-slate-900">{message.content}</span>
                </div>
              ) : message.type === 'agent' ? (
                <div className="flex items-start gap-2">
                  <Bot className={`w-4 h-4 mt-0.5 ${getAgentColor(message.agent)}`} />
                  <div>
                    <span className={`font-semibold ${getAgentColor(message.agent)}`}>
                      {getAgentName(message.agent)}:
                    </span>{' '}
                    <span className="text-slate-700">{message.content}</span>
                  </div>
                </div>
              ) : (
                <span className="text-slate-500 italic">{message.content}</span>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input - Fixed at bottom */}
      <div className="border-t border-slate-200 p-3 flex-shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Chat with VeriFlow agents..."
            className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}