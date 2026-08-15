import React, { useState, useEffect } from 'react';
import { useSession } from '../../context/SessionContext';
import { reportApi } from '../../services/api';
import axios from 'axios';
import { FileDown, Plus, Layers, User, Briefcase, Terminal } from 'lucide-react';
import { Modal } from '../common/Modal';

const BackendStatusBadge = () => {
  const [online, setOnline] = useState(true);
  const [showHelpModal, setShowHelpModal] = useState(false);

  useEffect(() => {
    const checkBackend = () => {
      axios
        .get('/api/health', { timeout: 3000 })
        .then(() => setOnline(true))
        .catch(() => setOnline(false));
    };

    checkBackend();
    const timer = setInterval(checkBackend, 8000);
    return () => clearInterval(timer);
  }, []);

  return (
    <>
      <button
        onClick={() => !online && setShowHelpModal(true)}
        className={`hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium border transition-all ${
          online
            ? 'text-emerald-700 bg-emerald-50 border-emerald-200/80 cursor-default'
            : 'text-rose-700 bg-rose-50 border-rose-200 animate-pulse hover:bg-rose-100 cursor-pointer'
        }`}
        title={online ? 'FastAPI Backend is Online' : 'Click to see how to start backend'}
      >
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            online ? 'bg-emerald-500' : 'bg-rose-500'
          }`}
        />
        <span>{online ? 'API Online' : 'API Offline (Port 8000)'}</span>
      </button>

      {/* Backend Help Modal */}
      <Modal
        isOpen={showHelpModal}
        onClose={() => setShowHelpModal(false)}
        title="Start Backend Server"
        maxWidth="max-w-md"
      >
        <div className="space-y-3 text-xs text-slate-600">
          <p>
            The frontend is active, but the Python backend at <b>http://127.0.0.1:8000</b> is unreachable.
          </p>

          <div className="space-y-1.5">
            <div className="font-semibold text-slate-800 flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-slate-600" />
              <span>Start on Windows:</span>
            </div>
            <div className="bg-slate-900 text-slate-100 p-2.5 rounded-lg font-mono text-[11px]">
              Double-click <b>run.bat</b> or run: <span className="text-emerald-400">python run.py</span>
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="font-semibold text-slate-800 flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-slate-600" />
              <span>Start on macOS / Linux:</span>
            </div>
            <div className="bg-slate-900 text-slate-100 p-2.5 rounded-lg font-mono text-[11px]">
              <span className="text-purple-300">./run.sh</span> or <span className="text-emerald-400">python3 run.py</span>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
};

export const Header = () => {
  const {
    sessions,
    currentSessionId,
    setCurrentSessionId,
    createNewSession,
    resumeData,
    jdData,
    resumeScore,
    matchData,
    showToast,
  } = useSession();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [exporting, setExporting] = useState(false);

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!newSessionName.trim()) return;
    await createNewSession(newSessionName.trim());
    setNewSessionName('');
    setIsModalOpen(false);
  };

  const handleExportReport = async () => {
    try {
      setExporting(true);
      showToast('Generating PDF report...');
      const response = await reportApi.exportPdf(currentSessionId, {
        resume: resumeData,
        jd: jdData,
        resume_score: resumeScore,
        match: matchData,
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Interview_Prep_Report_${resumeData?.name?.replace(/\s+/g, '_') || 'Candidate'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      showToast('PDF report downloaded successfully.');
    } catch (err) {
      console.error('Export error:', err);
      showToast('Failed to export PDF report.', 'error');
    } finally {
      setExporting(false);
    }
  };

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-5 flex items-center justify-between sticky top-0 z-10">
      {/* Session Switcher & Active Profile Context */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={currentSessionId}
            onChange={(e) => setCurrentSessionId(e.target.value)}
            className="text-xs font-medium bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1 text-slate-700 hover:bg-slate-100 transition-colors focus:ring-1 focus:ring-blue-500 focus:outline-none cursor-pointer"
          >
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <button
            onClick={() => setIsModalOpen(true)}
            className="p-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors border border-slate-200"
            title="Create New Session"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Active Candidate & Target Job Indicators */}
        <div className="hidden lg:flex items-center gap-2 pl-3 border-l border-slate-200 text-xs">
          <div className="flex items-center gap-1.5 text-slate-600 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/60">
            <User className="w-3 h-3 text-slate-500" />
            <span className="font-medium text-slate-700">{resumeData?.name || 'No resume'}</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-600 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/60">
            <Briefcase className="w-3 h-3 text-slate-500" />
            <span className="font-medium text-slate-700 truncate max-w-[180px]">
              {jdData?.title || 'No target job'}
            </span>
          </div>
        </div>
      </div>

      {/* Backend Status & Quick Action Button */}
      <div className="flex items-center gap-2.5">
        <BackendStatusBadge />
        <button
          onClick={handleExportReport}
          disabled={exporting}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 active:bg-blue-800 rounded-md transition-all disabled:opacity-50"
        >
          <FileDown className="w-3.5 h-3.5" />
          <span>{exporting ? 'Exporting...' : 'Export PDF'}</span>
        </button>
      </div>

      {/* New Session Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New Session"
        maxWidth="max-w-md"
      >
        <form onSubmit={handleCreateSession} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Session Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Frontend Engineer Prep"
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-200 rounded-md focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Creates a fresh workspace with independent resume analysis, job match, questions, and mock history.
            </p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-md"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-md"
            >
              Create Session
            </button>
          </div>
        </form>
      </Modal>
    </header>
  );
};
