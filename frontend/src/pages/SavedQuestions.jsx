import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { questionsApi } from '../services/api';
import {
  BookmarkCheck,
  Trash2,
  Mic,
  Search,
  Bookmark
} from 'lucide-react';
import { Badge } from '../components/common/Badge';

export const SavedQuestions = () => {
  const navigate = useNavigate();
  const { currentSessionId, showToast } = useSession();
  const [saved, setSaved] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const loadSaved = () => {
    setLoading(true);
    questionsApi
      .getSaved(currentSessionId)
      .then((res) => {
        setSaved(res.data || []);
      })
      .catch((err) => {
        console.error(err);
        showToast('Failed to load saved questions.', 'error');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSaved();
  }, [currentSessionId]);

  const handleRemoveBookmark = async (q) => {
    try {
      await questionsApi.toggleBookmark(q, currentSessionId);
      setSaved((prev) => prev.filter((item) => item.id !== q.id));
      showToast('Removed question from saved bank.');
    } catch (err) {
      showToast('Failed to remove bookmark.', 'error');
    }
  };

  const filtered = saved.filter(
    (q) =>
      q.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.skill.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Saved Questions</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Review and practice your pinned interview questions.
          </p>
        </div>

        {/* Search */}
        <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 shadow-sm w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search saved questions or skills..."
            className="w-full text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none"
          />
        </div>
      </div>

      {/* List */}
      <div className="space-y-3">
        {filtered.length > 0 ? (
          filtered.map((q, idx) => (
            <div
              key={q.id || idx}
              className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2.5 hover:border-slate-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <Badge variant={q.difficulty?.toLowerCase()} size="xs">{q.difficulty}</Badge>
                    <Badge variant="primary" size="xs">{q.skill}</Badge>
                    {q.based_on && <span className="text-[11px] text-slate-400">Based on: {q.based_on}</span>}
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 leading-snug">{q.question}</h3>
                </div>

                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <button
                    onClick={() => navigate('/mock-interview', { state: { selectedQuestion: q } })}
                    className="flex items-center gap-1 px-2.5 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold rounded-md transition-colors"
                  >
                    <Mic className="w-3 h-3" />
                    <span>Practice</span>
                  </button>
                  <button
                    onClick={() => handleRemoveBookmark(q)}
                    className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                    title="Remove from saved"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {q.why_this_question && (
                <p className="text-xs text-slate-500 pt-1 border-t border-slate-100">
                  <b>Rationale:</b> {q.why_this_question}
                </p>
              )}
            </div>
          ))
        ) : (
          <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
            <Bookmark className="w-8 h-8 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-700">No saved questions</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Click the bookmark icon on any question in "Questions" or "Project Deep-Dive" to pin it here for focused practice.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
