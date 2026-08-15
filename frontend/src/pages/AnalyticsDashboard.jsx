import React, { useState, useEffect } from 'react';
import { useSession } from '../context/SessionContext';
import { analyticsApi } from '../services/api';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  CartesianGrid,
} from 'recharts';
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Target,
  Mic,
  Cpu,
  Award
} from 'lucide-react';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';

export const AnalyticsDashboard = () => {
  const { currentSessionId, showToast } = useSession();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    analyticsApi
      .getAnalytics(currentSessionId)
      .then((res) => {
        setData(res.data);
      })
      .catch((err) => {
        console.error(err);
        showToast('Failed to load analytics.', 'error');
      })
      .finally(() => setLoading(false));
  }, [currentSessionId]);

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-500">Loading readiness analytics...</div>;
  }

  if (!data) return null;

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Performance Analytics</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Readiness metrics derived from resume structure, job description overlap, and mock interview answers.
          </p>
        </div>
      </div>

      {/* Top Readiness Score Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row items-center gap-6 pb-5 border-b border-slate-100">
          <ScoreRing
            score={data.interview_readiness_score}
            size={88}
            strokeWidth={7}
            label="Readiness"
          />
          <div className="space-y-1.5 flex-1 text-center sm:text-left">
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
              <h3 className="text-base font-bold text-slate-900">Overall Interview Readiness</h3>
              <Badge variant={data.interview_readiness_score >= 75 ? 'success' : 'warning'}>
                {data.interview_readiness_score >= 75 ? 'Interview Ready' : 'Preparation Active'}
              </Badge>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
              Composite score weighted across Resume Structure ({data.resume_score}/100), Target Match ({data.jd_match_percentage}%), Technical Depth ({data.technical_score}/100), Communication Clarity ({data.communication_score}/100), and Behavioral ownership ({data.behavioral_score}/100).
            </p>
          </div>
        </div>

        {/* 6 Key Performance Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 pt-4">
          {[
            { label: "Resume Score", val: `${data.resume_score}/100`, icon: FileText },
            { label: "Job Match", val: `${data.jd_match_percentage}%`, icon: Target },
            { label: "Mock Avg", val: `${data.average_interview_score}/100`, icon: Mic },
            { label: "Technical", val: `${data.technical_score}/100`, icon: Cpu },
            { label: "Communication", val: `${data.communication_score}/100`, icon: Award },
            { label: "Questions Attempted", val: data.questions_attempted, icon: CheckCircle2 },
          ].map((m, idx) => {
            const Icon = m.icon;
            return (
              <div key={idx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-center">
                <Icon className="w-3.5 h-3.5 text-slate-500 mx-auto mb-1" />
                <div className="text-[11px] text-slate-500">{m.label}</div>
                <div className="text-sm font-bold text-slate-800 mt-0.5">{m.val}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Radar Assessment */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">Competency Balance</h3>
            <span className="text-[11px] text-slate-400">5-axis evaluation</span>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={data.category_performance}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="category" tick={{ fill: '#475569', fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#cbd5e1" />
                <Radar
                  name="Score"
                  dataKey="score"
                  stroke="#2563eb"
                  fill="#3b82f6"
                  fillOpacity={0.25}
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Score Trend Line */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">Mock Score Progression</h3>
            <span className="text-[11px] text-slate-400">By attempt</span>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.score_trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="attempt" stroke="#94a3b8" fontSize={11} />
                <YAxis domain={[40, 100]} stroke="#94a3b8" fontSize={11} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#2563eb' }}
                  name="Overall Score"
                />
                <Line
                  type="monotone"
                  dataKey="technical"
                  stroke="#0891b2"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  name="Technical Depth"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Priority Weak Topic Detection & Mastered Strengths */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Weak Areas */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
          <div className="flex items-center gap-1.5 text-rose-700 font-bold text-xs uppercase tracking-wide">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
            <span>Priority Improvement Areas</span>
          </div>
          <div className="space-y-1.5">
            {data.weak_areas?.map((item, idx) => (
              <div
                key={idx}
                className="p-2.5 bg-rose-50/40 rounded-lg border border-rose-100 flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-semibold text-slate-800">{item.topic}</span>
                  <div className="text-[11px] text-slate-500">Average: {item.score}%</div>
                </div>
                <Badge variant={item.priority === 'High' ? 'danger' : 'warning'} size="xs">
                  {item.priority} Priority
                </Badge>
              </div>
            ))}
            {data.weak_areas?.length === 0 && (
              <p className="text-xs text-slate-500 italic p-2">No critical weak areas detected.</p>
            )}
          </div>
        </div>

        {/* Mastered Strong Areas */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
          <div className="flex items-center gap-1.5 text-emerald-700 font-bold text-xs uppercase tracking-wide">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Mastered Strengths</span>
          </div>
          <div className="space-y-1.5">
            {data.strong_areas?.map((item, idx) => (
              <div
                key={idx}
                className="p-2.5 bg-emerald-50/40 rounded-lg border border-emerald-100 flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-semibold text-slate-800">{item.topic}</span>
                  <div className="text-[11px] text-slate-500">Average: {item.score}%</div>
                </div>
                <Badge variant="success" size="xs">
                  {item.status}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
