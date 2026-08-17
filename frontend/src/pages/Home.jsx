import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { analyticsApi, interviewApi, resumeApi } from '../services/api';
import {
  FileText,
  Target,
  HelpCircle,
  Mic,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  ChevronRight,
  UploadCloud,
  Code2,
  MessageSquare,
  Compass,
  Check,
  Zap,
  Layers,
  BarChart3,
  Trash2,
  RotateCcw
} from 'lucide-react';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';

export const Home = () => {
  const navigate = useNavigate();
  const {
    resumeData,
    jdData,
    resumeScore,
    matchData,
    questions,
    currentSessionId,
    loadSampleData,
    loading,
    clearActiveResume,
    setResumeData,
    showToast
  } = useSession();

  const [analytics, setAnalytics] = useState(null);
  const [historyCount, setHistoryCount] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const [homeUploading, setHomeUploading] = useState(false);

  const handleHomeUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 1. Frontend validation: PDF format check
    const fileName = file.name || '';
    if (!fileName.toLowerCase().endsWith('.pdf')) {
      const msg = 'Invalid file. Please upload a valid resume PDF.';
      setUploadError(msg);
      showToast(msg, 'error');
      e.target.value = '';
      return;
    }

    // 2. Frontend validation: Empty file check
    if (file.size === 0) {
      const msg = 'Invalid file. The uploaded file is empty. Please upload a valid resume PDF.';
      setUploadError(msg);
      showToast(msg, 'error');
      e.target.value = '';
      return;
    }

    try {
      setHomeUploading(true);
      setUploadError(null);
      showToast(`Validating and extracting ${file.name}...`, 'info');
      const res = await resumeApi.upload(file);
      await setResumeData(res.data);
      showToast('Resume verified and loaded successfully.', 'success');
    } catch (err) {
      console.error('Home upload error:', err);
      const detail = err.response?.data?.detail;
      let msg = 'Invalid file. Please upload a valid resume PDF.';
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail)) {
        msg = detail.map((d) => d.msg || d.message).filter(Boolean).join(', ') || msg;
      } else if (detail?.message) {
        msg = detail.message;
      } else if (err.message) {
        msg = err.message;
      }
      setUploadError(msg);
      showToast(msg, 'error');
    } finally {
      setHomeUploading(false);
      e.target.value = '';
    }
  };

  useEffect(() => {
    if (currentSessionId && resumeData) {
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
    } else {
      setAnalytics(null);
      setHistoryCount(0);
    }
  }, [currentSessionId, resumeData]);

  // Explicit resume state machine
  let resumeStatus = 'NO_RESUME';
  if (homeUploading) {
    resumeStatus = 'PROCESSING';
  } else if (uploadError) {
    resumeStatus = 'INVALID_RESUME';
  } else if (resumeData && (resumeData.id || resumeData.skills?.length > 0)) {
    resumeStatus = 'RESUME_READY';
  } else {
    resumeStatus = 'NO_RESUME';
  }

  // Determine readiness score strictly from genuine active data
  const questionsPracticed = analytics?.questions_attempted ?? historyCount;
  const readinessScore = resumeStatus === 'RESUME_READY'
    ? (analytics?.interview_readiness_score ?? (resumeScore ? resumeScore.overall_score : null))
    : null;


  // Genuine strengths extracted strictly from active resume
  const strongAreas = resumeStatus === 'RESUME_READY' && resumeData?.skills?.length
    ? (matchData?.matching_skills?.length
        ? matchData.matching_skills.slice(0, 5)
        : resumeData.skills.slice(0, 5))
    : [];

  // Genuine gaps extracted strictly from resume vs target JD comparison
  const rawImprovement = (resumeStatus === 'RESUME_READY' && jdData && matchData?.missing_skills?.length)
    ? matchData.missing_skills.slice(0, 5)
    : [];

  const strongSet = new Set(strongAreas.map((s) => s.toLowerCase().trim()));
  const improvementAreas = rawImprovement.filter(
    (area) => !strongSet.has(area.toLowerCase().trim())
  );

  const totalQuestions = questions?.length || 0;

  // Determine active recommended milestone in the roadmap
  let activeStep = 1;
  if (resumeStatus !== 'RESUME_READY') {
    activeStep = 1;
  } else if (!jdData) {
    activeStep = 2;
  } else if (totalQuestions === 0) {
    activeStep = 3;
  } else {
    activeStep = 4;
  }

  // Helper for progress bar color
  const getProgressColor = (score) => {
    if (score >= 75) return 'bg-emerald-500';
    if (score >= 50) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Interview Preparation</h1>
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${
                resumeStatus === 'RESUME_READY'
                  ? 'bg-blue-50 text-blue-700 border-blue-200/60'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}
            >
              <Sparkles className={`w-3 h-3 ${resumeStatus === 'RESUME_READY' ? 'text-blue-500' : 'text-slate-400'}`} />
              {resumeStatus === 'RESUME_READY' ? 'Workspace Active' : 'Ready for Resume'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Prepare for your target role using your resume, job description, personalized questions, and mock interviews.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {resumeStatus === 'RESUME_READY' ? (
            <>
              <button
                onClick={() => navigate('/resume')}
                className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 shadow-sm transition-all hover:border-slate-300"
              >
                <FileText className="w-3.5 h-3.5 text-slate-500" />
                <span>Analyze Resume</span>
              </button>
              <button
                onClick={() => navigate('/questions')}
                className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 shadow-sm transition-all hover:border-slate-300"
              >
                <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
                <span>Generate Questions</span>
              </button>
              <button
                onClick={() => navigate('/mock-interview')}
                className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-sm shadow-blue-500/20 transition-all hover:shadow-md hover:shadow-blue-500/25"
              >
                <Mic className="w-3.5 h-3.5 text-white" />
                <span>Start Mock Interview</span>
              </button>
            </>
          ) : (
            <>
              <button
                onClick={loadSampleData}
                disabled={loading || homeUploading}
                className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-800 text-xs font-medium rounded-lg border border-slate-200 shadow-sm transition-all disabled:opacity-50"
                title="Load sample candidate (Alex Chen) to test workflows"
              >
                <Zap className="w-3.5 h-3.5 text-amber-500" />
                <span>{loading ? 'Loading Demo...' : 'Load Sample Profile'}</span>
              </button>
              <label className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm shadow-blue-500/20 transition-all hover:shadow-md hover:shadow-blue-500/25 cursor-pointer">
                <UploadCloud className="w-3.5 h-3.5 text-white" />
                <span>Upload Resume</span>
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleHomeUpload}
                  disabled={homeUploading}
                  className="hidden"
                />
              </label>
            </>
          )}
        </div>
      </div>

      {/* Validation Error Banner if upload rejected on Home */}
      {resumeStatus === 'INVALID_RESUME' && (
        <div className="p-5 bg-rose-50 border-2 border-rose-300 rounded-xl flex items-start gap-4 text-xs text-rose-950 shadow-sm animate-fadeIn">
          <div className="w-10 h-10 rounded-full bg-rose-100 border border-rose-300 flex items-center justify-center text-rose-700 flex-shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="space-y-2 flex-1">
            <div>
              <h3 className="text-sm font-bold text-rose-900">Upload Validation Error</h3>
              <p className="text-xs text-rose-800 leading-relaxed mt-1 font-medium">
                {uploadError}
              </p>
            </div>
            <div className="p-3 bg-white/90 rounded-lg border border-rose-200 text-[11px] text-rose-900 space-y-1">
              <div className="font-semibold">Expected Resume / CV Document:</div>
              <p className="text-slate-600">
                Please upload a genuine resume PDF containing your <b>Education</b>, <b>Technical Skills</b>, <b>Work Experience</b>, or <b>Projects</b>. (Non-resume documents such as academic research papers, certificates, textbooks, project reports, and invoices are rejected).
              </p>
            </div>
            <div className="pt-1 flex flex-wrap items-center gap-3">
              <label className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white rounded-lg text-xs font-semibold cursor-pointer transition-colors shadow-sm">
                <UploadCloud className="w-4 h-4" />
                <span>Upload Another Resume</span>
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleHomeUpload}
                  disabled={homeUploading}
                  className="hidden"
                />
              </label>
              <label className="inline-flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-xs font-medium cursor-pointer transition-colors shadow-2xs">
                <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
                <span>Try Again</span>
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleHomeUpload}
                  disabled={homeUploading}
                  className="hidden"
                />
              </label>
              <button
                onClick={() => setUploadError(null)}
                className="text-xs text-slate-500 hover:text-slate-800 font-medium px-2 py-1"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Processing State Banner */}
      {resumeStatus === 'PROCESSING' && (
        <div className="bg-white border border-blue-200 rounded-xl p-6 sm:p-7 shadow-sm space-y-4 animate-pulse">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
              <UploadCloud className="w-4 h-4 animate-bounce" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Analyzing your resume...</h3>
              <p className="text-xs text-slate-500">Validating document format and extracting technical skills & projects.</p>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="p-2.5 rounded-lg bg-blue-50/70 border border-blue-100 text-xs text-blue-800 font-medium">✓ Document uploaded</div>
            <div className="p-2.5 rounded-lg bg-blue-50/70 border border-blue-100 text-xs text-blue-800 font-medium">✓ Format validated</div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 font-medium">⏳ Extracting skills</div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 font-medium">⏳ Building profile</div>
          </div>
        </div>
      )}

      {/* Hero Section: Conditional */}
      {resumeStatus !== 'RESUME_READY' ? (
        /* Empty Dashboard / Clean Onboarding State */
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 sm:p-7 shadow-sm">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              {/* Left 8 cols: Onboarding Message & Upload CTA */}
              <div className="lg:col-span-8 space-y-4">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200/70">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Resume Analysis</span>
                </div>
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 leading-snug">
                  Upload your resume to unlock personalized interview insights, strengths, skill gaps, and performance analytics.
                </h2>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-2xl">
                  The AI validates your document, extracts your verified technical competencies, matches you against target job requirements, and generates grounded mock interview questions with zero hallucination.
                </p>

                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <label className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm shadow-blue-500/20 transition-all hover:shadow-md hover:shadow-blue-500/25 cursor-pointer">
                    <UploadCloud className="w-4 h-4 text-white" />
                    <span>{homeUploading ? 'Validating Resume...' : 'Upload Resume (PDF only)'}</span>
                    <input
                      type="file"
                      accept=".pdf,application/pdf"
                      onChange={handleHomeUpload}
                      disabled={homeUploading}
                      className="hidden"
                    />
                  </label>
                  <button
                    onClick={loadSampleData}
                    disabled={loading || homeUploading}
                    className="flex items-center gap-1.5 px-3.5 py-2.5 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium rounded-lg border border-slate-200 transition-colors"
                  >
                    <span>Or try with sample profile (Alex Chen)</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                  </button>
                </div>
              </div>

              {/* Right 4 cols: Feature Highlights */}
              <div className="lg:col-span-4 lg:border-l lg:border-slate-100 lg:pl-6 space-y-2.5">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Workspace Capabilities
                </span>
                {[
                  { title: 'Verified Strengths', desc: 'Extracted directly from your resume' },
                  { title: 'ATS Resume Audit', desc: 'Category-level scoring & keyword review' },
                  { title: 'Job Match Analysis', desc: 'Identify verified matching skills & gaps' },
                  { title: 'Personalized Q&A', desc: 'Grounded in your real project highlights' },
                ].map((feat, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 text-xs">
                    <div className="w-4 h-4 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0 mt-0.5 border border-emerald-200">
                      <Check className="w-2.5 h-2.5" />
                    </div>
                    <div>
                      <span className="font-semibold text-slate-800">{feat.title}</span>
                      <p className="text-[11px] text-slate-500">{feat.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Active Resume Workspace Content */
        <div className="space-y-6">
          {/* Active Context Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              {/* Left Context: Selected Resume & Target Job */}
              <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Resume Tile */}
                <div className="p-4 rounded-lg bg-slate-50/80 border border-slate-200/80 hover:border-slate-300 transition-all flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      <span className="flex items-center gap-1.5 text-slate-500">
                        <FileText className="w-3.5 h-3.5 text-blue-600" />
                        Active Resume
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => navigate('/resume')}
                          className="text-[11px] text-blue-600 hover:text-blue-700 font-medium lowercase tracking-normal flex items-center gap-0.5"
                        >
                          change <ChevronRight className="w-3 h-3" />
                        </button>
                        <button
                          onClick={clearActiveResume}
                          className="text-[11px] text-rose-500 hover:text-rose-700 font-medium lowercase tracking-normal flex items-center gap-0.5"
                          title="Remove active resume from workspace"
                        >
                          <Trash2 className="w-3 h-3" /> remove
                        </button>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <h3 className="text-sm font-bold text-slate-800 truncate" title={resumeData.name || resumeData.title}>
                          {resumeData.filename || resumeData.name || 'Uploaded Resume'}
                        </h3>
                        <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80 px-1.5 py-0.5 rounded">
                          ✓ Valid ({Math.round((resumeData.resume_confidence || 0.95) * 100)}%)
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 font-mono mt-1 truncate">
                        ID: {resumeData.id ? `${resumeData.id.slice(0, 10)}...` : 'active'} {resumeData.resume_hash ? `| SHA: ${resumeData.resume_hash.slice(0, 8)}...` : ''}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 pt-2.5 border-t border-slate-200/60 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">Extracted Skills</span>
                    <span className="font-semibold text-slate-700">
                      {resumeData.skills?.length || 0} skills identified
                    </span>
                  </div>
                </div>

                {/* Target Job Tile */}
                <div className="p-4 rounded-lg bg-slate-50/80 border border-slate-200/80 hover:border-slate-300 transition-all flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      <span className="flex items-center gap-1.5 text-slate-500">
                        <Target className="w-3.5 h-3.5 text-indigo-600" />
                        Target Role
                      </span>
                      <button
                        onClick={() => navigate('/match')}
                        className="text-[11px] text-blue-600 hover:text-blue-700 font-medium lowercase tracking-normal flex items-center gap-0.5"
                      >
                        {jdData ? 'view / change' : 'set'} <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>
                    {jdData ? (
                      <div>
                        <h3 className="text-sm font-bold text-slate-800 truncate" title={jdData.title}>
                          {jdData.title}
                        </h3>
                        <p className="text-xs text-slate-500 truncate mt-0.5">
                          {jdData.company ? `${jdData.company} • ` : ''}{jdData.experience_years || 'Requirements specified'}
                        </p>
                      </div>
                    ) : (
                      <div>
                        <p className="text-xs font-semibold text-slate-700">No target role set</p>
                        <p className="text-[11px] text-slate-500 mt-0.5">Add job description for skill alignment</p>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 pt-2.5 border-t border-slate-200/60 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">Role Alignment</span>
                    <span className="font-semibold text-slate-700">
                      {matchData ? `${matchData.match_percentage}% match` : 'Not matched yet'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Right Summary: Readiness Gauge */}
              <div className="lg:col-span-4 lg:border-l lg:border-slate-100 lg:pl-6 flex items-center justify-between sm:justify-end gap-5">
                <div className="text-left lg:text-right space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Overall Readiness
                  </span>
                  <div className="text-sm font-bold text-slate-900">
                    {readinessScore !== null
                      ? (readinessScore >= 80 ? 'Interview Ready' : readinessScore >= 60 ? 'Moderate Readiness' : 'In Preparation')
                      : 'Pending Analysis'}
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {questionsPracticed > 0
                      ? `${questionsPracticed} mock answers evaluated`
                      : 'No mock answers recorded yet'}
                  </p>
                </div>
                <ScoreRing
                  score={readinessScore || 0}
                  size={72}
                  strokeWidth={7}
                  label="Readiness"
                />
              </div>
            </div>
          </div>

          {/* Balanced 4-Metric Performance Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Metric 1: Resume Quality */}
            <div
              onClick={() => navigate('/resume')}
              className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:border-slate-300 hover:shadow transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600">Resume Quality</span>
                <div className="p-1.5 rounded-md bg-blue-50 text-blue-600">
                  <FileText className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="mt-2.5 flex items-baseline gap-2">
                <span className="text-xl font-bold text-slate-900">
                  {resumeScore ? `${resumeScore.overall_score}/100` : '—'}
                </span>
                <span className="text-[11px] text-slate-500 font-medium">
                  {resumeScore
                    ? (resumeScore.overall_score >= 80 ? 'Strong structure' : 'Needs review')
                    : 'Calculating...'}
                </span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    resumeScore ? getProgressColor(resumeScore.overall_score) : 'bg-slate-200'
                  }`}
                  style={{ width: `${resumeScore?.overall_score || 0}%` }}
                />
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-blue-600 transition-colors">
                <span>{resumeScore ? 'View ATS audit' : 'Analyze resume'}</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </div>

            {/* Metric 2: Job Match */}
            <div
              onClick={() => navigate('/match')}
              className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:border-slate-300 hover:shadow transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600">Job Match</span>
                <div className="p-1.5 rounded-md bg-indigo-50 text-indigo-600">
                  <Target className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="mt-2.5 flex items-baseline gap-2">
                <span className="text-xl font-bold text-slate-900">
                  {matchData ? `${matchData.match_percentage}%` : '—'}
                </span>
                <span className="text-[11px] text-slate-500 font-medium">
                  {matchData ? `${matchData.matching_skills?.length || 0} matching skills` : 'Add target role'}
                </span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    matchData ? getProgressColor(matchData.match_percentage) : 'bg-slate-200'
                  }`}
                  style={{ width: `${matchData?.match_percentage || 0}%` }}
                />
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-indigo-600 transition-colors">
                <span>{matchData ? 'Skill alignment' : 'Compare with JD'}</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </div>

            {/* Metric 3: Technical Depth */}
            <div
              onClick={() => navigate('/mock-interview')}
              className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:border-slate-300 hover:shadow transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600">Technical Depth</span>
                <div className="p-1.5 rounded-md bg-emerald-50 text-emerald-600">
                  <Code2 className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="mt-2.5 flex items-baseline gap-2">
                <span className="text-xl font-bold text-slate-900">
                  {questionsPracticed > 0 && analytics?.technical_score > 0
                    ? `${analytics.technical_score}/100`
                    : '—'}
                </span>
                <span className="text-[11px] text-slate-500 font-medium">
                  {questionsPracticed > 0 && analytics?.technical_score > 0
                    ? 'From mock answers'
                    : 'Complete mock interview'}
                </span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    questionsPracticed > 0 && analytics?.technical_score > 0
                      ? getProgressColor(analytics.technical_score)
                      : 'bg-slate-200'
                  }`}
                  style={{
                    width: `${questionsPracticed > 0 && analytics?.technical_score > 0 ? analytics.technical_score : 0}%`
                  }}
                />
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-emerald-600 transition-colors">
                <span>{questionsPracticed > 0 ? 'Review technical answers' : 'Practice technical answers'}</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </div>

            {/* Metric 4: Communication & Delivery */}
            <div
              onClick={() => navigate('/mock-interview')}
              className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:border-slate-300 hover:shadow transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600">Communication</span>
                <div className="p-1.5 rounded-md bg-amber-50 text-amber-600">
                  <MessageSquare className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="mt-2.5 flex items-baseline gap-2">
                <span className="text-xl font-bold text-slate-900">
                  {questionsPracticed > 0 && analytics?.communication_score > 0
                    ? `${analytics.communication_score}/100`
                    : '—'}
                </span>
                <span className="text-[11px] text-slate-500 font-medium">
                  {questionsPracticed > 0 && analytics?.communication_score > 0
                    ? 'Clarity & structure'
                    : 'Complete mock interview'}
                </span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    questionsPracticed > 0 && analytics?.communication_score > 0
                      ? getProgressColor(analytics.communication_score)
                      : 'bg-slate-200'
                  }`}
                  style={{
                    width: `${questionsPracticed > 0 && analytics?.communication_score > 0 ? analytics.communication_score : 0}%`
                  }}
                />
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-amber-600 transition-colors">
                <span>{questionsPracticed > 0 ? 'Review delivery' : 'Simulate voice answer'}</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </div>
          </div>

          {/* Strong Areas vs Needs Improvement (Genuine Resume-Derived Data Only) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Strong Areas */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Verified Strengths</span>
                  </h3>
                  <span className="text-[11px] text-slate-400 font-medium">
                    {strongAreas.length} competencies
                  </span>
                </div>

                <p className="text-xs text-slate-600">
                  Demonstrated skills extracted from your active resume:
                </p>

                {strongAreas.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {strongAreas.map((skill, idx) => (
                      <Badge key={idx} variant="success" size="sm">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 rounded-lg text-center text-xs text-slate-500 border border-slate-100">
                    No verified technical skills detected in current resume.
                  </div>
                )}
              </div>

              <div className="pt-2 text-[11px] text-slate-400 border-t border-slate-100 flex items-center justify-between">
                <span>Keep reinforcing core strengths</span>
                <button
                  onClick={() => navigate('/resume')}
                  className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-0.5"
                >
                  view all skills <ChevronRight className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Priority Focus Areas (Derived strictly from target JD gaps) */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Priority Focus Gaps</span>
                  </h3>
                  <span className="text-[11px] text-slate-400 font-medium">
                    {improvementAreas.length} target gaps
                  </span>
                </div>

                <p className="text-xs text-slate-600">
                  {jdData
                    ? 'Target requirements and technical gaps identified against job description:'
                    : 'Add a target job description to reveal missing requirements and prep topics.'}
                </p>

                {improvementAreas.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {improvementAreas.map((area, idx) => (
                      <Badge key={idx} variant="warning" size="sm">
                        {area}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 rounded-lg text-center text-xs text-slate-500 border border-slate-100">
                    {jdData
                      ? 'No critical skill gaps identified against target job description.'
                      : 'Add a target job description to uncover missing requirements and recommended prep topics.'}
                  </div>
                )}
              </div>

              <div className="pt-2 text-[11px] text-slate-400 border-t border-slate-100 flex items-center justify-between">
                <span>Focus questions on these topics</span>
                <button
                  onClick={() => navigate(jdData ? '/questions' : '/match')}
                  className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-0.5"
                >
                  {jdData ? 'generate focused Qs' : 'add target job'} <ChevronRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Guided Preparation Roadmap */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-blue-600" />
              <span>Preparation Roadmap</span>
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Follow these core milestones to maximize your interview readiness score.
            </p>
          </div>
          <span className="text-xs font-semibold text-slate-600 hidden sm:inline-block">
            Step {activeStep} of 4 Active
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
          {/* Step 1: Resume */}
          <div
            onClick={() => navigate('/resume')}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer relative ${
              resumeStatus === 'RESUME_READY'
                ? 'bg-slate-50/60 border-slate-200 hover:bg-slate-100/60'
                : activeStep === 1
                ? 'bg-blue-50/40 border-blue-400 ring-2 ring-blue-500/10'
                : 'bg-white border-dashed border-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-bold text-slate-800">1. Resume Analysis</span>
              {resumeStatus === 'RESUME_READY' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <span className="text-[10px] bg-blue-600 text-white font-bold px-1.5 py-0.5 rounded">Start</span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              {resumeStatus === 'RESUME_READY' ? `${resumeData.name || 'Candidate profile'} loaded` : 'Upload PDF/DOCX to extract skills'}
            </p>
            {activeStep === 1 && resumeStatus !== 'RESUME_READY' && (
              <div className="mt-2 text-[10px] text-blue-600 font-semibold flex items-center gap-1">
                <span>Upload resume to begin</span> <ArrowRight className="w-3 h-3" />
              </div>
            )}
          </div>

          {/* Step 2: Job Description */}
          <div
            onClick={() => navigate('/match')}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer relative ${
              jdData
                ? 'bg-slate-50/60 border-slate-200 hover:bg-slate-100/60'
                : activeStep === 2
                ? 'bg-blue-50/40 border-blue-400 ring-2 ring-blue-500/10'
                : 'bg-white border-dashed border-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-bold text-slate-800">2. Job Match</span>
              {jdData ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <span className="text-[10px] bg-slate-200 text-slate-600 font-bold px-1.5 py-0.5 rounded">
                  {resumeStatus === 'RESUME_READY' ? 'Action' : 'Step 2'}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              {jdData ? `${jdData.title}` : 'Compare requirements & gaps'}
            </p>
            {activeStep === 2 && (
              <div className="mt-2 text-[10px] text-blue-600 font-semibold flex items-center gap-1">
                <span>Recommended Next Step</span> <ArrowRight className="w-3 h-3" />
              </div>
            )}
          </div>

          {/* Step 3: Generate Questions */}
          <div
            onClick={() => navigate('/questions')}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer relative ${
              totalQuestions > 0
                ? 'bg-slate-50/60 border-slate-200 hover:bg-slate-100/60'
                : activeStep === 3
                ? 'bg-blue-50/40 border-blue-400 ring-2 ring-blue-500/10'
                : 'bg-white border-dashed border-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-bold text-slate-800">3. Question Bank</span>
              {totalQuestions > 0 ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <span className="text-[10px] bg-slate-200 text-slate-600 font-bold px-1.5 py-0.5 rounded">
                  {resumeStatus === 'RESUME_READY' ? 'Action' : 'Step 3'}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              {totalQuestions > 0 ? `${totalQuestions} questions generated` : 'Create grounded interview questions'}
            </p>
            {activeStep === 3 && (
              <div className="mt-2 text-[10px] text-blue-600 font-semibold flex items-center gap-1">
                <span>Recommended Next Step</span> <ArrowRight className="w-3 h-3" />
              </div>
            )}
          </div>

          {/* Step 4: Mock Interview */}
          <div
            onClick={() => navigate('/mock-interview')}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer relative ${
              questionsPracticed >= (totalQuestions || 5) && questionsPracticed > 0
                ? 'bg-slate-50/60 border-slate-200 hover:bg-slate-100/60'
                : activeStep === 4
                ? 'bg-blue-50/40 border-blue-400 ring-2 ring-blue-500/10'
                : 'bg-white border-dashed border-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-bold text-slate-800">4. Mock Interview</span>
              {questionsPracticed >= (totalQuestions || 5) && questionsPracticed > 0 ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : questionsPracticed > 0 ? (
                <span className="text-[10px] bg-blue-100 text-blue-700 font-bold px-1.5 py-0.5 rounded">
                  {questionsPracticed} done
                </span>
              ) : (
                <span className="text-[10px] bg-slate-200 text-slate-600 font-bold px-1.5 py-0.5 rounded">
                  Step 4
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              {questionsPracticed > 0 ? `${questionsPracticed} answers evaluated` : 'Simulate live interview answers'}
            </p>
            {activeStep === 4 && (
              <div className="mt-2 text-[10px] text-blue-600 font-semibold flex items-center gap-1">
                <span>{questionsPracticed > 0 ? 'Continue mock prep' : 'Recommended Next Step'}</span> <ArrowRight className="w-3 h-3" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
