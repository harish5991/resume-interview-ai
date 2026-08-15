import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { interviewApi } from '../services/api';
import {
  BookOpen,
  ArrowLeft
} from 'lucide-react';
import { Badge } from '../components/common/Badge';

export const PreparationMode = () => {
  const navigate = useNavigate();
  const { resumeData, jdData, showToast } = useSession();
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (resumeData) {
      setLoading(true);
      interviewApi
        .getTopics(resumeData, jdData)
        .then((res) => {
          setTopics(res.data || []);
        })
        .catch((err) => {
          console.error(err);
          showToast('Failed to load preparation topics.', 'error');
        })
        .finally(() => setLoading(false));
    }
  }, [resumeData, jdData]);

  return (
    <div className="space-y-6 pb-12">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/skill-gap')}
              className="text-slate-400 hover:text-slate-600 p-1 rounded transition-colors"
              title="Back to Skill Gap"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Top 10 Preparation Topics</h1>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 ml-6">
            Targeted study blueprint curated for your profile and target role.
          </p>
        </div>

        <button
          onClick={() => navigate('/skill-gap')}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
        >
          View Full Skill Gap Analysis
        </button>
      </div>

      {/* Topics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {topics.map((t, idx) => (
          <div key={idx} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">
                    #{idx + 1}
                  </span>
                  <Badge variant={t.importance === 'High' ? 'hard' : 'medium'} size="xs">
                    {t.importance} Priority
                  </Badge>
                </div>
                <h3 className="text-sm font-bold text-slate-900 leading-snug">{t.topic}</h3>
              </div>
              <span className="text-[11px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-100 whitespace-nowrap">
                {t.recommended_level}
              </span>
            </div>

            <div className="space-y-0.5 text-xs text-slate-600">
              <span className="font-semibold text-slate-700">Why It Matters:</span>
              <p className="leading-relaxed">{t.why_it_matters}</p>
            </div>

            <div className="space-y-0.5 text-xs text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100">
              <span className="font-semibold text-slate-700">Resume Evidence:</span>
              <p className="italic text-slate-600">{t.resume_evidence}</p>
            </div>

            <div className="pt-1.5 border-t border-slate-100 space-y-1 text-xs">
              <span className="font-semibold text-slate-700">Expected Interview Questions:</span>
              <ul className="space-y-0.5 text-slate-600">
                {t.expected_questions?.map((q, qidx) => (
                  <li key={qidx} className="flex items-start gap-1">
                    <span className="text-blue-500 font-bold">•</span>
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
