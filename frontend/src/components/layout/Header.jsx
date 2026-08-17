import React, { useState, useEffect } from 'react';
import { useSession } from '../../context/SessionContext';
import { reportApi } from '../../services/api';
import axios from 'axios';
import {
  FileDown,
  Plus,
  Layers,
  User,
  Briefcase,
  Terminal,
  Trash2,
  Settings,
  ShieldCheck,
  CheckCircle2,
  RotateCcw
} from 'lucide-react';
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
    deleteSession,
    autoClearOnClose,
    setAutoClearOnClose,
    resumeData,
    jdData,
    resumeScore,
    matchData,
    resetAllSessions,
    showToast,
  } = useSession();

  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [isManageModalOpen, setIsManageModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [newSessionName, setNewSessionName] = useState('');
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!newSessionName.trim()) return;
    await createNewSession(newSessionName.trim());
    setNewSessionName('');
    setIsNewModalOpen(false);
  };

  const confirmDeleteSession = async () => {
    if (!sessionToDelete) return;
    try {
      setDeleting(true);
      await deleteSession(sessionToDelete.id);
      setSessionToDelete(null);
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(false);
    }
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
      {/* Session Switcher */}
      <div className="flex items-center gap-1.5">
        <Layers className="w-3.5 h-3.5 text-slate-400" />
        <select
          value={currentSessionId}
          onChange={(e) => setCurrentSessionId(e.target.value)}
          className="text-xs font-medium bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1 text-slate-700 hover:bg-slate-100 transition-colors focus:ring-1 focus:ring-blue-500 focus:outline-none cursor-pointer max-w-[180px] sm:max-w-[220px] truncate"
        >
          {sessions.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <button
          onClick={() => setIsNewModalOpen(true)}
          className="p-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors border border-slate-200"
          title="Create New Session"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setIsManageModalOpen(true)}
          className="p-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors border border-slate-200"
          title="Manage Sessions & Preferences"
        >
          <Settings className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Backend Status & Quick Action Button */}
      <div className="flex items-center gap-2.5">
        <BackendStatusBadge />
        <button
          onClick={handleExportReport}
          disabled={exporting || !resumeData}
          title={!resumeData ? 'Upload a resume to export PDF report' : 'Export PDF Report'}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 active:bg-blue-800 rounded-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <FileDown className="w-3.5 h-3.5" />
          <span>{exporting ? 'Exporting...' : 'Export PDF'}</span>
        </button>
      </div>

      {/* New Session Modal */}
      <Modal
        isOpen={isNewModalOpen}
        onClose={() => setIsNewModalOpen(false)}
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
              onClick={() => setIsNewModalOpen(false)}
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

      {/* Manage Sessions & Preferences Modal */}
      <Modal
        isOpen={isManageModalOpen}
        onClose={() => setIsManageModalOpen(false)}
        title="Manage Workspaces & Retention"
        maxWidth="max-w-lg"
      >
        <div className="space-y-5 text-xs">
          {/* Privacy & Auto-Clear Setting Card */}
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-slate-800">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                <span>Auto-Clear History on Application Close</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoClearOnClose}
                  onChange={(e) => setAutoClearOnClose(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed font-normal">
              {autoClearOnClose
                ? '🔒 Ephemeral Privacy Mode: When you close the browser window or tab, mock answers and score evaluations are automatically wiped.'
                : '💾 Persistent Mode: Answers, scores, and questions remain saved in the local database across application restarts.'}
            </p>
          </div>

          {/* Sessions List */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800 uppercase tracking-wide text-[11px]">
                Active Workspaces ({sessions.length})
              </span>
              <div className="flex items-center gap-3">
                {sessions.length > 1 && (
                  <button
                    onClick={async () => {
                      if (window.confirm('Clear all custom sessions and reset to default workspace?')) {
                        await resetAllSessions();
                        setIsManageModalOpen(false);
                      }
                    }}
                    className="text-rose-600 hover:text-rose-700 font-semibold text-[11px] flex items-center gap-1 transition-colors"
                    title="Clear all custom sessions and reset to default"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Reset to Default</span>
                  </button>
                )}
                <button
                  onClick={() => {
                    setIsManageModalOpen(false);
                    setIsNewModalOpen(true);
                  }}
                  className="text-blue-600 hover:text-blue-700 font-semibold text-[11px] flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add Workspace</span>
                </button>
              </div>
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {sessions.map((s) => {
                const isActive = s.id === currentSessionId;
                return (
                  <div
                    key={s.id}
                    className={`p-3 rounded-lg border flex items-center justify-between gap-3 transition-all ${
                      isActive
                        ? 'bg-blue-50/50 border-blue-200'
                        : 'bg-white border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <div className="space-y-0.5 flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-800 text-xs truncate">{s.name}</span>
                        {isActive && (
                          <span className="text-[10px] bg-blue-600 text-white font-bold px-1.5 py-0.2 rounded">
                            Active
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 block truncate">ID: {s.id}</span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {!isActive && (
                        <button
                          onClick={() => setCurrentSessionId(s.id)}
                          className="px-2.5 py-1 text-[11px] font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-100 rounded-md transition-colors shadow-2xs"
                        >
                          Switch
                        </button>
                      )}

                      {sessions.length > 1 && (
                        <button
                          onClick={() => setSessionToDelete(s)}
                          className="p-1.5 text-rose-600 hover:text-rose-800 hover:bg-rose-50 rounded-md border border-rose-100 transition-colors"
                          title="Delete Session"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex justify-end pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsManageModalOpen(false)}
              className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={Boolean(sessionToDelete)}
        onClose={() => setSessionToDelete(null)}
        title="Delete Workspace Session?"
        maxWidth="max-w-md"
      >
        <div className="space-y-3 text-xs text-slate-600">
          <p>
            Are you sure you want to delete <b>"{sessionToDelete?.name}"</b>?
          </p>
          <p className="text-[11px] text-slate-500">
            This will permanently remove this workspace and all associated mock interview answers, question history, and evaluations.
          </p>
          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={() => setSessionToDelete(null)}
              className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={confirmDeleteSession}
              disabled={deleting}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-md shadow-sm"
            >
              {deleting ? 'Deleting...' : 'Yes, Delete Session'}
            </button>
          </div>
        </div>
      </Modal>
    </header>
  );
};
