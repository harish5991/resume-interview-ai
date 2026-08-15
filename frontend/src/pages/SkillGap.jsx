import React, { useState, useEffect } from 'react';
import { useSession } from '../context/SessionContext';
import { analyticsApi, interviewApi } from '../services/api';
import {
  GitPullRequest,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  Clock
} from 'lucide-react';
import { Badge } from '../components/common/Badge';

export const SkillGap = () => {
  const { resumeData, jdData, showToast } = useSession();
  const [skillGap, setSkillGap] = useState(null);
  const [topics, setTopics] = useState([]);
  const [activeTab, setActiveTab] = useState('roadmap'); // roadmap | topics
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (resumeData && jdData) {
      setLoading(true);
      Promise.all([
        analyticsApi.getSkillGap(resumeData, jdData),
        interviewApi.getTopics(resumeData, jdData),
      ])
        .then(([gapRes, topicsRes]) => {
          setSkillGap(gapRes.data);
          setTopics(topicsRes.data || []);
        })
        .catch((err) => {
          console.error(err);
          showToast('Failed to fetch skill gap analysis.', 'error');
        })
        .finally(() => setLoading(false));
    }
  }, [resumeData, jdData]);

  return (
    <div className="space-y-6 pb-12">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Skill Gap & Preparation Topics</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Compare verified resume competencies against target job requirements to prioritize interview study topics.
          </p>
        </div>
      </div>

      {/* Loading state */}
      {loading ? (
        <div className="p-8 bg-white rounded-xl border border-slate-200 text-center text-xs text-slate-500">
          Loading skill gap analysis & preparation topics...
        </div>
      ) : skillGap ? (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Target Role Alignment Summary
            </h3>
            <span className="text-[11px] text-slate-400">{jdData?.title || 'Target Role'}</span>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed max-w-4xl">
            {skillGap.summary}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {/* Matching Skills */}
            <div className="p-3 bg-emerald-50/40 rounded-lg border border-emerald-100 space-y-1.5">
              <div className="flex items-center gap-1.5 text-emerald-800 font-bold text-xs">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Matching Verified Skills ({skillGap.matching_skills?.length || 0})</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {skillGap.matching_skills?.map((s, idx) => (
                  <Badge key={idx} variant="success" size="xs">
                    {s}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Missing Skills */}
            <div className="p-3 bg-rose-50/40 rounded-lg border border-rose-100 space-y-1.5">
              <div className="flex items-center gap-1.5 text-rose-800 font-bold text-xs">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                <span>Missing Target Requirements ({skillGap.missing_skills?.length || 0})</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {skillGap.missing_skills?.map((s, idx) => (
                  <Badge key={idx} variant="danger" size="xs">
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
          <GitPullRequest className="w-8 h-8 text-slate-300 mx-auto" />
          <h4 className="text-sm font-bold text-slate-700">No skill comparison available</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Upload your resume and select a target job description to compute missing skills and study roadmaps.
          </p>
        </div>
      )}

      {/* Tabs: Learning Roadmap vs Top Prep Topics */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('roadmap')}
            className={`pb-2.5 transition-colors relative ${
              activeTab === 'roadmap'
                ? 'text-blue-600 font-bold border-b-2 border-blue-600'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Learning Roadmap ({skillGap?.learning_roadmap?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('topics')}
            className={`pb-2.5 transition-colors relative ${
              activeTab === 'topics'
                ? 'text-blue-600 font-bold border-b-2 border-blue-600'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Top 10 Prep Topics ({topics.length})
          </button>
        </nav>
      </div>

      {/* Roadmap Tab */}
      {activeTab === 'roadmap' && (
        <div className="space-y-3">
          {skillGap?.learning_roadmap && skillGap.learning_roadmap.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {skillGap.learning_roadmap.map((item, idx) => (
                <div key={idx} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <h4 className="text-xs font-bold text-slate-900">{item.skill}</h4>
                      <Badge variant={item.importance === 'High' ? 'hard' : 'medium'} size="xs">
                        {item.importance}
                      </Badge>
                    </div>
                    <span className="flex items-center gap-1 text-[11px] font-medium text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                      <Clock className="w-3 h-3 text-slate-400" />
                      ~{item.estimated_hours}h study
                    </span>
                  </div>

                  <div className="space-y-0.5">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Key Concepts:</span>
                    <ul className="space-y-0.5 text-xs text-slate-600">
                      {item.key_topics?.map((topic, tidx) => (
                        <li key={tidx} className="flex items-start gap-1">
                          <span className="text-blue-500 font-bold">•</span>
                          <span>{topic}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="pt-1.5 border-t border-slate-100 space-y-0.5">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Recommended Resources:</span>
                    <ul className="space-y-0.5 text-xs text-slate-600">
                      {item.learning_resources?.map((res, ridx) => (
                        <li key={ridx} className="flex items-start gap-1 text-slate-700">
                          <BookOpen className="w-3 h-3 flex-shrink-0 mt-0.5 text-slate-400" />
                          <span>{res}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 bg-white rounded-xl border border-slate-200 text-center text-xs text-slate-500">
              No skill gaps detected. Your resume skills cover all target job requirements.
            </div>
          )}
        </div>
      )}

      {/* Top Prep Topics Tab */}
      {activeTab === 'topics' && (
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
      )}
    </div>
  );
};
