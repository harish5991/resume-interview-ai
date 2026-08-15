import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { interviewApi } from '../services/api';
import {
  History,
  CheckCircle2,
  AlertCircle,
  Mic,
  Trash2,
  ShieldCheck
} from 'lucide-react';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';

export const QuestionHistory = () => {
  const navigate = useNavigate();
  const { currentSessionId, clearSessionHistory, showToast } = useSession();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [clearing, setClearing] = useState(false);

  const fetchHistory = () => {
    setLoading(true);
    interviewApi
      .getHistory(currentSessionId)
      .then((res) => {
        setHistory(res.data || []);
      })
      .catch((err) => {
        console.error(err);
        showToast('Failed to load question history.', 'error');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHistory();
  }, [currentSessionId]);

  const handleClearHistory = async () => {
    try {
      setClearing(true);
      await clearSessionHistory();
      setHistory([]);
      setIsClearModalOpen(false);
      showToast('Interview history cleared.');
    } catch (err) {
      console.error(err);
      showToast('Failed to clear history.', 'error');
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Question History</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Review previous mock interview answers, scoring evaluations, and model responses.
          </p>
        </div>

        {history.length > 0 && (
          <button
            onClick={() => setIsClearModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200/70 rounded-lg transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Session Privacy Banner */}
      <div className="flex items-center gap-2.5 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600">
        <ShieldCheck className="w-4 h-4 text-slate-500 shrink-0" />
        <span>
          <b>Session Scoped:</b> Interview attempts are saved locally to your active session and reset when the session is cleared.
        </span>
      </div>

      {/* History List */}
      <div className="space-y-4">
        {history.length > 0 ? (
          history.map((item, idx) => (
            <div
              key={item.id || idx}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3 border-b border-slate-100">
                <div className="space-y-1 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">
                      #{idx + 1}
                    </span>
                    <Badge variant={item.difficulty?.toLowerCase() || 'medium'} size="xs">
                      {item.difficulty || 'Medium'}
                    </Badge>
                    <Badge variant="primary" size="xs">{item.skill || 'Technical'}</Badge>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 leading-snug">
                    {item.question_text || 'Interview Question'}
                  </h3>
                </div>

                <div className="flex items-center gap-2">
                  <ScoreRing score={item.overall_score || 75} size={56} strokeWidth={5} label="Score" />
                </div>
              </div>

              {/* Candidate Answer */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-0.5">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                  Your Answer:
                </span>
                <p className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed">
                  "{item.user_answer || 'No answer recording available.'}"
                </p>
              </div>

              {/* Feedback Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                {/* Strengths */}
                <div className="p-2.5 bg-emerald-50/40 rounded-lg border border-emerald-100 space-y-1">
                  <span className="font-bold text-emerald-800">Strengths:</span>
                  <ul className="space-y-0.5 text-slate-700">
                    {item.strengths?.map((s, sidx) => (
                      <li key={sidx} className="flex items-start gap-1">
                        <span className="text-emerald-500 font-bold">•</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Growth */}
                <div className="p-2.5 bg-amber-50/40 rounded-lg border border-amber-100 space-y-1">
                  <span className="font-bold text-amber-800">Growth Areas:</span>
                  <ul className="space-y-0.5 text-slate-700">
                    {item.weaknesses?.map((w, widx) => (
                      <li key={widx} className="flex items-start gap-1">
                        <span className="text-amber-500 font-bold">•</span>
                        <span>{w}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Model Answer */}
              {item.improved_answer && (
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-xs text-slate-600 italic">
                  <span className="font-semibold text-slate-700 not-italic">Model Answer: </span>
                  "{item.improved_answer}"
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
            <History className="w-8 h-8 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-700">No mock interview attempts yet</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Go to "Mock Interview" and submit your answers to build your interview evaluation transcript.
            </p>
            <button
              onClick={() => navigate('/mock-interview')}
              className="mt-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Start Mock Interview</span>
            </button>
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      <Modal
        isOpen={isClearModalOpen}
        onClose={() => setIsClearModalOpen(false)}
        title="Clear Interview History?"
        maxWidth="max-w-md"
      >
        <div className="space-y-4 text-xs text-slate-600">
          <p>
            Are you sure you want to clear all mock interview attempts recorded in this session? This action cannot be undone.
          </p>
          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={() => setIsClearModalOpen(false)}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={handleClearHistory}
              disabled={clearing}
              className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-md shadow-sm"
            >
              {clearing ? 'Clearing...' : 'Yes, Clear All'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
