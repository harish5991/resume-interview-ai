import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { analyticsApi } from '../services/api';
import {
  Copy,
  Check,
  ArrowLeft
} from 'lucide-react';
import { Badge } from '../components/common/Badge';

export const ResumeImprovement = () => {
  const navigate = useNavigate();
  const { resumeData, showToast } = useSession();
  const [improvements, setImprovements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState(null);

  useEffect(() => {
    if (resumeData) {
      setLoading(true);
      analyticsApi
        .getImprovements(resumeData)
        .then((res) => {
          setImprovements(res.data || []);
        })
        .catch((err) => {
          console.error(err);
          showToast('Failed to load resume suggestions.', 'error');
        })
        .finally(() => setLoading(false));
    }
  }, [resumeData]);

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    showToast('Example bullet point copied.');
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/resume')}
              className="text-slate-400 hover:text-slate-600 p-1 rounded transition-colors"
              title="Back to Resume"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Resume Improvement Suggestions</h1>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 ml-6">
            Actionable advice on impact metrics, power verbs, and keyword alignment.
          </p>
        </div>

        <button
          onClick={() => navigate('/resume')}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
        >
          View Full Resume Analysis
        </button>
      </div>

      {/* Suggestions List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading resume suggestions...</div>
        ) : improvements.length > 0 ? (
          improvements.map((item, idx) => (
            <div key={idx} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={item.impact_level === 'High' ? 'danger' : 'warning'} size="xs">
                      {item.impact_level} Impact
                    </Badge>
                    <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                      {item.category}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900">{item.issue}</h3>
                </div>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                <b>Recommendation:</b> {item.suggestion}
              </p>

              {/* Before vs After */}
              {item.example_before && item.example_after && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  {/* Before */}
                  <div className="p-3 bg-rose-50/50 rounded-lg border border-rose-100 space-y-1">
                    <span className="text-[11px] font-bold text-rose-800 uppercase tracking-wide">
                      Original / Passive:
                    </span>
                    <p className="text-xs text-slate-700 italic">
                      "{item.example_before}"
                    </p>
                  </div>

                  {/* After */}
                  <div className="p-3 bg-emerald-50/50 rounded-lg border border-emerald-100 space-y-1 relative">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wide">
                        Improved High-Impact:
                      </span>
                      <button
                        onClick={() => handleCopy(item.example_after, idx)}
                        className="text-slate-400 hover:text-emerald-700 p-1 rounded transition-colors"
                        title="Copy improved bullet"
                      >
                        {copiedIdx === idx ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <p className="text-xs text-slate-800 font-medium">
                      "{item.example_after}"
                    </p>
                  </div>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="p-8 bg-white rounded-xl border border-slate-200 text-center text-xs text-slate-500">
            No improvement suggestions available for this resume.
          </div>
        )}
      </div>
    </div>
  );
};
