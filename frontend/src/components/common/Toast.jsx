import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export const Toast = ({ toast, onClose }) => {
  if (!toast) return null;

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0" />,
    info: <Info className="w-5 h-5 text-brand-500 flex-shrink-0" />
  };

  const bgClasses = {
    success: "bg-white border-emerald-200 text-slate-800 shadow-lg shadow-emerald-500/10",
    error: "bg-white border-rose-200 text-slate-800 shadow-lg shadow-rose-500/10",
    info: "bg-white border-brand-200 text-slate-800 shadow-lg shadow-brand-500/10"
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-bounce-in max-w-md">
      <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${bgClasses[toast.type] || bgClasses.info}`}>
        {icons[toast.type] || icons.info}
        <p className="text-sm font-medium pr-2">{toast.message}</p>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 p-1 rounded-lg transition-colors ml-auto"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export const Modal = ({ isOpen, onClose, title, children, maxWidth = "max-w-2xl" }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className={`bg-white rounded-2xl border border-slate-200 shadow-2xl w-full ${maxWidth} overflow-hidden transform transition-all`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 max-h-[75vh] overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
};
