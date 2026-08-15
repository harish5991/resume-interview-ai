import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { analyticsApi, interviewApi } from '../services/api';
import {
  FileText,
  Target,
  HelpCircle,
  Mic,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';

export const Home = () => {
  const navigate = useNavigate();
  const { resumeData, jdData, resumeScore, matchData, questions, currentSessionId } = useSession();
  const [analytics, setAnalytics] = useState(null);
  const [historyCount, setHistoryCount] = useState(0);

  useEffect(() => {
    analyticsApi
      .getAnalytics(currentSessionId)
      .then((res) => {
        if (res.data) setAnalytics(res.data);
      })
      .catch(() => {});

    interviewApi
      .getHistory(currentSessionId)
      .then((res) => {
        if (res.data && Array.isArray(res.data)) {
          setHistoryCount(res.data.length);
        }
      })
      .catch(() => {});
  }, [currentSessionId]);

  // Determine readiness score
  const readinessScore = analytics?.interview_readiness_score ?? (
    resumeScore && matchData
      ? Math.round((resumeScore.overall_score * 0.4) + (matchData.match_percentage * 0.4) + ((historyCount > 0 ? 80 : 50) * 0.2))
      : (resumeScore ? Math.round(resumeScore.overall_score * 0.7) : null)
  );

  // Strong & Needs Improvement skills/topics
  const strongAreas = analytics?.strong_areas?.length
    ? analytics.strong_areas.map((a) => (typeof a === 'string' ? a : a.topic))
    : matchData?.matching_skills?.length
    ? matchData.matching_skills.slice(0, 5)
    : resumeData?.skills?.slice(0, 4) || [];

  const improvementAreas = analytics?.weak_areas?.length
    ? analytics.weak_areas.map((a) => (typeof a === 'string' ? a : a.topic))
    : matchData?.missing_skills?.length
    ? matchData.missing_skills.slice(0, 5)
    : resumeScore?.improvement_areas?.slice(0, 3) || [];

  const questionsPracticed = analytics?.questions_attempted ?? historyCount;

  return (
    <div className="space-y-6 pb-12">
      {/* Workspace Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Interview Preparation</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Prepare for your target role using your resume, job description, personalized questions, and mock interviews.
          </p>
        </div>

        {/* Primary Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => navigate('/resume')}
            className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 shadow-sm transition-colors"
          >
            <FileText className="w-3.5 h-3.5 text-slate-500" />
            <span>Analyze Resume</span>
          </button>
          <button
            onClick={() => navigate('/questions')}
            className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 shadow-sm transition-colors"
          >
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
            <span>Generate Questions</span>
          </button>
          <button
            onClick={() => navigate('/mock-interview')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            <Mic className="w-3.5 h-3.5 text-white" />
            <span>Start Mock Interview</span>
          </button>
        </div>
      </div>

      {/* Current Context Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          {/* Selected Resume */}
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Selected Resume
            </span>
            {resumeData ? (
              <div>
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <span>{resumeData.name || resumeData.title || 'Uploaded Resume'}</span>
                </h3>
                <p className="text-xs text-slate-500 truncate max-w-xs mt-0.5">
                  {resumeData.summary || `${resumeData.skills?.length || 0} extracted skills`}
                </p>
              </div>
            ) : (
              <div>
                <p className="text-xs font-semibold text-slate-700">No resume uploaded</p>
                <button
                  onClick={() => navigate('/resume')}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium underline mt-0.5 inline-block"
                >
                  Upload resume to start
                </button>
              </div>
            )}
          </div>

          {/* Target Job */}
          <div className="space-y-1 md:border-l md:border-slate-100 md:pl-6">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Target Job
            </span>
            {jdData ? (
              <div>
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-slate-600 flex-shrink-0" />
                  <span className="truncate max-w-xs">{jdData.title}</span>
                </h3>
                <p className="text-xs text-slate-500 truncate max-w-xs mt-0.5">
                  {jdData.company ? `${jdData.company} • ` : ''}{jdData.experience_years || 'Requirements specified'}
                </p>
              </div>
            ) : (
              <div>
                <p className="text-xs font-semibold text-slate-700">No target job set</p>
                <button
                  onClick={() => navigate('/match')}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium underline mt-0.5 inline-block"
                >
                  Add job description
                </button>
              </div>
            )}
          </div>

          {/* Readiness Summary */}
          <div className="flex items-center justify-between md:justify-end gap-4 md:border-l md:border-slate-100 md:pl-6">
            <div className="text-left md:text-right">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Readiness Status
              </span>
              <span className="text-xs font-bold text-slate-800 mt-0.5 block">
                {readinessScore !== null
                  ? (readinessScore >= 75 ? 'Interview Ready' : 'In Preparation')
                  : 'Pending Analysis'}
              </span>
              <span className="text-[11px] text-slate-500">
                {questionsPracticed} questions practiced
              </span>
            </div>
            <ScoreRing
              score={readinessScore || 0}
              size={64}
              strokeWidth={6}
              label="Readiness"
            />
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Metric 1: Resume Score */}
        <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-sm">
          <div className="text-[11px] text-slate-500 font-medium">Resume Score</div>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {resumeScore ? `${resumeScore.overall_score}/100` : 'Not analyzed'}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {resumeScore ? (resumeScore.overall_score >= 80 ? 'Strong structure' : 'Needs review') : 'Upload resume'}
          </div>
        </div>

        {/* Metric 2: Job Match */}
        <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-sm">
          <div className="text-[11px] text-slate-500 font-medium">Job Match</div>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {matchData ? `${matchData.match_percentage}%` : (jdData ? 'Analyzing...' : 'Not matched')}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {matchData ? `${matchData.matching_skills?.length || 0} matching skills` : 'Add target JD'}
          </div>
        </div>

        {/* Metric 3: Interview Readiness */}
        <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-sm">
          <div className="text-[11px] text-slate-500 font-medium">Readiness</div>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {readinessScore !== null ? `${readinessScore}%` : 'Not analyzed'}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {readinessScore >= 75 ? 'Role aligned' : 'Practice recommended'}
          </div>
        </div>

        {/* Metric 4: Technical Depth */}
        <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-sm">
          <div className="text-[11px] text-slate-500 font-medium">Technical Depth</div>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {analytics?.technical_score
              ? `${analytics.technical_score}/100`
              : (resumeScore?.skills_score ? `${resumeScore.skills_score}/100` : 'Not evaluated')}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {analytics?.technical_score ? 'From mock answers' : 'From resume skills'}
          </div>
        </div>

        {/* Metric 5: Communication */}
        <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-sm">
          <div className="text-[11px] text-slate-500 font-medium">Communication</div>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {analytics?.communication_score
              ? `${analytics.communication_score}/100`
              : (questionsPracticed > 0 ? 'Evaluating' : 'Not practiced')}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {questionsPracticed > 0 ? 'Clarity & delivery' : 'Try mock answer'}
          </div>
        </div>

        {/* Metric 6: Questions Practiced */}
        <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-sm">
          <div className="text-[11px] text-slate-500 font-medium">Questions Practiced</div>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {questionsPracticed}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {questions?.length ? `${questions.length} available in set` : 'Generate questions'}
          </div>
        </div>
      </div>

      {/* Why Readiness Exists: Strong Areas vs Needs Improvement */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Strong Areas */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Strong Areas</span>
            </h3>
            <span className="text-[11px] text-slate-400">Verified competencies</span>
          </div>

          {strongAreas.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs text-slate-600">
                You demonstrated strong competency and match in the following areas:
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {strongAreas.map((skill, idx) => (
                  <Badge key={idx} variant="success" size="sm">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 bg-slate-50 rounded-lg text-center text-xs text-slate-500">
              Upload your resume and complete a match to identify verified strength areas.
            </div>
          )}
        </div>

        {/* Needs Improvement */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Needs Improvement</span>
            </h3>
            <span className="text-[11px] text-slate-400">Priority prep topics</span>
          </div>

          {improvementAreas.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs text-slate-600">
                Focus your preparation on these target requirements and gaps:
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {improvementAreas.map((area, idx) => (
                  <Badge key={idx} variant="warning" size="sm">
                    {area}
                  </Badge>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 bg-slate-50 rounded-lg text-center text-xs text-slate-500">
              No skill gaps detected yet. Add a target job description to uncover missing requirements.
            </div>
          )}
        </div>
      </div>

      {/* Preparation Workflow Steps */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
          Preparation Checklist
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
          {/* Step 1 */}
          <div
            onClick={() => navigate('/resume')}
            className={`p-3 rounded-lg border transition-colors cursor-pointer ${
              resumeData
                ? 'bg-slate-50/70 border-slate-200 hover:bg-slate-100/70'
                : 'bg-white border-dashed border-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700">1. Resume Analysis</span>
              {resumeData ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <span className="text-[10px] text-blue-600 font-semibold">Start</span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              {resumeData ? `${resumeData.name} loaded` : 'Upload PDF/DOCX to extract skills'}
            </p>
          </div>

          {/* Step 2 */}
          <div
            onClick={() => navigate('/match')}
            className={`p-3 rounded-lg border transition-colors cursor-pointer ${
              jdData
                ? 'bg-slate-50/70 border-slate-200 hover:bg-slate-100/70'
                : 'bg-white border-dashed border-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700">2. Job Description</span>
              {jdData ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <span className="text-[10px] text-blue-600 font-semibold">Match</span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              {jdData ? `${jdData.title}` : 'Compare requirements & gaps'}
            </p>
          </div>

          {/* Step 3 */}
          <div
            onClick={() => navigate('/questions')}
            className={`p-3 rounded-lg border transition-colors cursor-pointer ${
              questions && questions.length > 0
                ? 'bg-slate-50/70 border-slate-200 hover:bg-slate-100/70'
                : 'bg-white border-dashed border-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700">3. Generate Questions</span>
              {questions && questions.length > 0 ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <span className="text-[10px] text-blue-600 font-semibold">Generate</span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              {questions && questions.length > 0 ? `${questions.length} questions ready` : 'Create grounded interview questions'}
            </p>
          </div>

          {/* Step 4 */}
          <div
            onClick={() => navigate('/mock-interview')}
            className={`p-3 rounded-lg border transition-colors cursor-pointer ${
              questionsPracticed > 0
                ? 'bg-slate-50/70 border-slate-200 hover:bg-slate-100/70'
                : 'bg-white border-dashed border-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700">4. Mock Interview</span>
              {questionsPracticed > 0 ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <span className="text-[10px] text-blue-600 font-semibold">Practice</span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              {questionsPracticed > 0 ? `${questionsPracticed} answers scored` : 'Simulate live interview answers'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
