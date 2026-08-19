import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { resumeApi, analyticsApi, interviewApi } from '../services/api';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Code,
  Briefcase,
  GraduationCap,
  Award,
  Layers,
  Copy,
  Check,
  Cpu,
  Database,
  Shield,
  Zap,
  Terminal,
  Mic,
  GitBranch,
  Trash2,
  RotateCcw
} from 'lucide-react';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';
import { FALLBACK_RESUMES } from '../utils/fallbackData';

export const ResumeAnalysis = () => {
  const navigate = useNavigate();
  const { resumeData, setResumeData, clearActiveResume, resumeScore, showToast } = useSession();
  const [uploading, setUploading] = useState(false);
  const [samples, setSamples] = useState(FALLBACK_RESUMES);
  const [activeTab, setActiveTab] = useState('overview'); // overview | extracted | improvements | deepdive
  
  // Extracted sub-tab
  const [extractedSubTab, setExtractedSubTab] = useState('skills');

  // Resume improvements state
  const [improvements, setImprovements] = useState([]);
  const [loadingImprovements, setLoadingImprovements] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState(null);

  // Project deep dive state
  const [selectedProjectIndex, setSelectedProjectIndex] = useState(0);
  const [deepDiveData, setDeepDiveData] = useState(null);
  const [loadingDeepDive, setLoadingDeepDive] = useState(false);

  // Load samples
  useEffect(() => {
    resumeApi
      .getSamples()
      .then((res) => {
        if (res.data && res.data.length > 0) {
          setSamples(res.data);
        }
      })
      .catch(() => {});
  }, []);

  // Fetch improvements when tab changes
  useEffect(() => {
    if (activeTab === 'improvements' && resumeData) {
      setLoadingImprovements(true);
      analyticsApi
        .getImprovements(resumeData)
        .then((res) => setImprovements(res.data || []))
        .catch(() => showToast('Failed to load resume suggestions.', 'error'))
        .finally(() => setLoadingImprovements(false));
    }
  }, [activeTab, resumeData]);

  // Fetch deep dive when project or tab changes
  const projects = resumeData?.projects || [];
  const currentProject = projects[selectedProjectIndex];

  useEffect(() => {
    if (activeTab === 'deepdive' && currentProject) {
      setLoadingDeepDive(true);
      interviewApi
        .getProjectDeepDive(
          currentProject.title,
          currentProject.technologies,
          currentProject.description || currentProject.highlights?.join(' ')
        )
        .then((res) => setDeepDiveData(res.data))
        .catch(() => showToast('Failed to load project deep dive.', 'error'))
        .finally(() => setLoadingDeepDive(false));
    }
  }, [activeTab, selectedProjectIndex, resumeData]);

  const [uploadError, setUploadError] = useState(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 1. Frontend validation: PDF check
    const fileName = file.name || '';
    if (!fileName.toLowerCase().endsWith('.pdf')) {
      const msg = 'Invalid file. Please upload a valid resume PDF.';
      setUploadError(msg);
      showToast(msg, 'error');
      e.target.value = '';
      return;
    }

    // 2. Frontend validation: Empty check
    if (file.size === 0) {
      const msg = 'Invalid file. The uploaded file is empty. Please upload a valid resume PDF.';
      setUploadError(msg);
      showToast(msg, 'error');
      e.target.value = '';
      return;
    }

    try {
      setUploading(true);
      setUploadError(null);
      showToast(`Uploading and validating ${file.name}...`, 'info');
      const res = await resumeApi.upload(file);
      await setResumeData(res.data);
      showToast('Resume parsed and verified successfully.', 'success');
    } catch (err) {
      console.error('Resume upload error:', err);
      const detail = err.response?.data?.detail;
      const isConnectionError =
        err.response?.data?.is_connection_error ||
        err.response?.status === 502 ||
        err.response?.status === 503 ||
        err.response?.status === 504 ||
        err.code === 'ECONNABORTED' ||
        err.code === 'ERR_NETWORK' ||
        err.message?.includes('timeout') ||
        err.message?.includes('Network Error');

      let msg = 'Invalid file. Please upload a valid resume PDF.';
      if (isConnectionError) {
        msg = err.message?.includes('timeout') || err.code === 'ECONNABORTED'
          ? 'Upload timed out. Please check if the backend server is running on http://127.0.0.1:8000.'
          : 'Backend server is offline or unreachable on http://127.0.0.1:8000. Please start the backend with "python run.py" or "./run.sh".';
      } else if (typeof detail === 'string') {
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
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleSelectSample = async (sample) => {
    setUploadError(null);
    await setResumeData(sample);
    showToast(`Loaded profile: ${sample.name}`);
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    showToast('Copied example to clipboard.');
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Resume Analysis</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Extract skills, work experience, and projects to evaluate quality and structure.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/match')}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors"
          >
            Compare with Job Description
          </button>
        </div>
      </div>

      {/* Validation / Server Error Banner if upload rejected */}
      {uploadError && (
        <div className="p-5 bg-rose-50 border-2 border-rose-300 rounded-xl flex items-start gap-4 text-xs text-rose-950 shadow-md animate-fadeIn">
          <div className="w-10 h-10 rounded-full bg-rose-100 border border-rose-300 flex items-center justify-center text-rose-700 flex-shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="space-y-2 flex-1">
            <div>
              <h3 className="text-sm font-bold text-rose-900">
                {uploadError?.toLowerCase().includes('offline') || uploadError?.toLowerCase().includes('timeout') || uploadError?.toLowerCase().includes('8000')
                  ? 'Server Connection / Timeout Error'
                  : 'Upload Validation Error'}
              </h3>
              <p className="text-xs text-rose-800 leading-relaxed mt-1 font-medium">
                {uploadError}
              </p>
            </div>
            {!(uploadError?.toLowerCase().includes('offline') || uploadError?.toLowerCase().includes('timeout') || uploadError?.toLowerCase().includes('8000')) && (
              <div className="p-3 bg-white/90 rounded-lg border border-rose-200 text-[11px] text-rose-900 space-y-1">
                <div className="font-semibold">Expected Resume / CV Document:</div>
                <p className="text-slate-600">
                  Please upload a genuine resume PDF containing your <b>Education</b>, <b>Technical Skills</b>, <b>Work Experience</b>, or <b>Projects</b>. (Non-resume documents such as academic research papers, certificates, textbooks, project reports, and invoices are rejected).
                </p>
              </div>
            )}
            <div className="pt-1 flex flex-wrap items-center gap-3">
              <label className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white rounded-lg text-xs font-semibold cursor-pointer transition-colors shadow-sm">
                <UploadCloud className="w-4 h-4" />
                <span>Upload Another Resume</span>
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="hidden"
                />
              </label>
              <label className="inline-flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-xs font-medium cursor-pointer transition-colors shadow-2xs">
                <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
                <span>Try Again</span>
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleFileUpload}
                  disabled={uploading}
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

      {/* Active Resume Status Bar */}
      {resumeData && (
        <div className="p-3 bg-white border border-slate-200 rounded-xl flex flex-wrap items-center justify-between gap-3 text-xs shadow-2xs">
          <div className="flex items-center gap-2 flex-wrap">
            <FileText className="w-4 h-4 text-blue-600" />
            <span className="font-bold text-slate-900">{resumeData.filename || resumeData.name + '_Resume.pdf'}</span>
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded text-[11px] font-semibold">
              ✓ Verified Resume ({Math.round((resumeData.resume_confidence || 0.95) * 100)}% Confidence)
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-slate-500 font-mono text-[11px]">
              ID: {resumeData.id ? `${resumeData.id.slice(0, 13)}...` : 'active'} {resumeData.resume_hash ? `| SHA: ${resumeData.resume_hash.slice(0, 8)}...` : ''}
            </span>
            <button
              onClick={clearActiveResume}
              className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100 rounded-md transition-colors"
              title="Remove resume and clear analysis"
            >
              <Trash2 className="w-3 h-3" />
              <span>Remove Resume</span>
            </button>
          </div>
        </div>
      )}

      {/* Upload Zone & Sample Profiles */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Upload Box */}
        <div className="lg:col-span-2 bg-white border-2 border-dashed border-slate-300 hover:border-slate-400 rounded-xl p-6 text-center transition-all bg-slate-50/40 hover:bg-white group relative">
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileUpload}
            disabled={uploading}
            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
          />
          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-800">
                {uploading ? 'Validating and parsing resume...' : 'Drop resume PDF here or click to browse'}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">Accepts text-based PDF resumes only (.pdf)</p>
            </div>
            {resumeData?.filename && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-200/60">
                <CheckCircle2 className="w-3 h-3" />
                Active: {resumeData.filename}
              </span>
            )}
          </div>
        </div>

        {/* Demo Sample Switcher */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
          <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wide">
            Sample Profiles
          </div>
          <p className="text-[11px] text-slate-500">
            Select a verified profile to test workflows:
          </p>

          <div className="space-y-1.5 pt-1">
            {samples.map((s) => (
              <button
                key={s.id}
                onClick={() => handleSelectSample(s)}
                className={`w-full text-left p-2 rounded-lg border text-xs transition-colors ${
                  resumeData?.name === s.name
                    ? 'border-blue-500 bg-blue-50/50 font-semibold text-blue-900'
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700'
                }`}
              >
                <div className="font-semibold text-slate-900">{s.name}</div>
                <div className="text-[11px] text-slate-500 truncate">{s.summary}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6 text-xs font-semibold">
          {[
            { id: 'overview', label: 'Overview & Score' },
            { id: 'extracted', label: 'Extracted Content' },
            { id: 'improvements', label: 'Resume Improvements' },
            { id: 'deepdive', label: 'Project Deep-Dive' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-2.5 transition-colors relative ${
                activeTab === tab.id
                  ? 'text-blue-600 font-bold border-b-2 border-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* TAB 1: Overview & Score */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {resumeScore ? (
            <>
              {/* Score Summary Card */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex flex-col sm:flex-row items-center gap-6 pb-5 border-b border-slate-100">
                  <ScoreRing score={resumeScore.overall_score} size={88} strokeWidth={7} label="Resume Score" />
                  <div className="space-y-1.5 flex-1 text-center sm:text-left">
                    <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                      <h3 className="text-base font-bold text-slate-900">Resume Quality Score</h3>
                      <Badge variant={resumeScore.overall_score >= 80 ? 'success' : 'warning'}>
                        {resumeScore.overall_score >= 80 ? 'Strong Structure' : 'Review Recommended'}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
                      {resumeScore.rationale}
                    </p>
                  </div>
                </div>

                {/* Sub-scores */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 pt-4">
                  {[
                    { label: "Skills", val: resumeScore.skills_score, icon: Code },
                    { label: "Projects", val: resumeScore.projects_score, icon: Layers },
                    { label: "Experience", val: resumeScore.experience_score, icon: Briefcase },
                    { label: "Education", val: resumeScore.education_score, icon: GraduationCap },
                    { label: "Completeness", val: resumeScore.completeness_score, icon: CheckCircle2 },
                    { label: "Job Relevance", val: resumeScore.relevance_score, icon: Award }
                  ].map((item, idx) => {
                    const Icon = item.icon;
                    return (
                      <div key={idx} className="bg-slate-50 rounded-lg p-2.5 border border-slate-100 text-center">
                        <Icon className="w-3.5 h-3.5 text-slate-500 mx-auto mb-1" />
                        <div className="text-[11px] text-slate-500">{item.label}</div>
                        <div className="text-sm font-bold text-slate-800 mt-0.5">{item.val}/100</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Strengths & Improvement Areas */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                  <div className="flex items-center gap-2 text-emerald-800 font-bold text-xs">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Verified Strengths</span>
                  </div>
                  <ul className="space-y-2">
                    {resumeScore.strengths.map((str, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 flex-shrink-0"></span>
                        <span>{str}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                  <div className="flex items-center gap-2 text-amber-800 font-bold text-xs">
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                    <span>Improvement Opportunities</span>
                  </div>
                  <ul className="space-y-2">
                    {resumeScore.improvement_areas.map((imp, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 flex-shrink-0"></span>
                        <span>{imp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
              <FileText className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-sm font-bold text-slate-700">No resume analyzed</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Upload your resume or choose a sample profile above to view structural scoring and category breakdowns.
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Extracted Content */}
      {activeTab === 'extracted' && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          {!resumeData ? (
            <div className="p-8 text-center space-y-2">
              <FileText className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-sm font-bold text-slate-700">No extracted resume data</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Upload your resume or choose a sample profile above to extract skills, projects, and work experience.
              </p>
            </div>
          ) : (
            <>
              <div className="flex border-b border-slate-200 gap-4 text-xs font-semibold">
                {['skills', 'projects', 'experience', 'raw_text'].map((subTab) => (
                  <button
                    key={subTab}
                    onClick={() => setExtractedSubTab(subTab)}
                    className={`pb-2 capitalize transition-colors ${
                      extractedSubTab === subTab
                        ? 'border-b-2 border-blue-600 text-blue-600'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    {subTab.replace('_', ' ')}
                  </button>
                ))}
              </div>

              {/* Sub-tab 1: Skills */}
              {extractedSubTab === 'skills' && (
                <div className="space-y-4 pt-2">
                  <div>
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wide block mb-2">
                      All Extracted Skills ({resumeData?.skills?.length || 0})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {resumeData?.skills?.map((s, idx) => (
                        <Badge key={idx} variant="primary" size="sm">
                          {s}
                        </Badge>
                      ))}
                      {!resumeData?.skills?.length && (
                        <span className="text-xs text-slate-500">No skills found in current resume.</span>
                      )}
                    </div>
                  </div>

                  {resumeData?.skill_categories && Object.keys(resumeData.skill_categories).length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-slate-100">
                      {Object.entries(resumeData.skill_categories).map(([cat, list]) => (
                        <div key={cat} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                          <h4 className="text-xs font-bold text-slate-700 mb-1">{cat}</h4>
                          <p className="text-xs text-slate-600">{list.join(', ')}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Sub-tab 2: Projects */}
              {extractedSubTab === 'projects' && (
                <div className="space-y-3 pt-2">
                  {resumeData?.projects?.map((p, idx) => (
                    <div key={idx} className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-slate-800 text-sm">{p.title}</h4>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {p.technologies?.map((t, tidx) => (
                          <Badge key={tidx} variant="neutral" size="xs">
                            {t}
                          </Badge>
                        ))}
                      </div>
                      <ul className="space-y-1 text-xs text-slate-600 pt-1">
                        {p.highlights?.map((h, hidx) => (
                          <li key={hidx} className="flex items-start gap-1.5">
                            <span className="text-blue-500 font-bold">•</span>
                            <span>{h}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                  {!resumeData?.projects?.length && (
                    <div className="p-4 text-center text-xs text-slate-500">No projects extracted.</div>
                  )}
                </div>
              )}

              {/* Sub-tab 3: Experience */}
              {extractedSubTab === 'experience' && (
                <div className="space-y-3 pt-2">
                  {resumeData?.experience?.map((exp, idx) => (
                    <div key={idx} className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-slate-800 text-sm">{exp.role}</h4>
                        <span className="text-xs text-slate-500">{exp.duration}</span>
                      </div>
                      <div className="text-xs font-semibold text-blue-700">{exp.company}</div>
                      <ul className="space-y-1 text-xs text-slate-600 pt-1">
                        {exp.responsibilities?.map((r, ridx) => (
                          <li key={ridx} className="flex items-start gap-1.5">
                            <span className="text-blue-500 font-bold">•</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                  {!resumeData?.experience?.length && (
                    <div className="p-4 text-center text-xs text-slate-500">No experience records extracted.</div>
                  )}
                </div>
              )}

              {/* Sub-tab 4: Raw Text */}
              {extractedSubTab === 'raw_text' && (
                <pre className="p-4 bg-slate-900 text-slate-100 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap font-mono max-h-96">
                  {resumeData?.raw_text || 'No raw text available.'}
                </pre>
              )}
            </>
          )}
        </div>
      )}

      {/* TAB 3: Resume Improvements */}
      {activeTab === 'improvements' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Actionable Bullet Improvements
            </h3>
            <span className="text-xs text-slate-400">Impact metric rewrites</span>
          </div>

          {!resumeData ? (
            <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
              <FileText className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-sm font-bold text-slate-700">No resume analyzed</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Upload your resume or choose a sample profile above to generate actionable bullet point suggestions.
              </p>
            </div>
          ) : loadingImprovements ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading suggestions...</div>
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
                    <h4 className="text-sm font-bold text-slate-900">{item.issue}</h4>
                  </div>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">
                  <b>Advice:</b> {item.suggestion}
                </p>

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
              No improvement suggestions available for this profile.
            </div>
          )}
        </div>
      )}

      {/* TAB 4: Project Deep-Dive */}
      {activeTab === 'deepdive' && (
        <div className="space-y-4">
          {!resumeData || projects.length === 0 ? (
            <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
              <Layers className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-sm font-bold text-slate-700">No projects available for deep-dive</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Upload a resume with project highlights to analyze architecture, database design, API design, and system trade-offs.
              </p>
            </div>
          ) : (
            <>
              {/* Project selector */}
              <div className="flex flex-wrap gap-2">
                {projects.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedProjectIndex(idx)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors flex items-center gap-1.5 ${
                      selectedProjectIndex === idx
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
                    }`}
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>{p.title}</span>
                  </button>
                ))}
              </div>

              {loadingDeepDive ? (
                <div className="p-8 text-center text-xs text-slate-500">Analyzing architecture details...</div>
              ) : deepDiveData ? (
                <div className="space-y-4">
                  {/* Architecture Grid */}
                  <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                      <div>
                        <h3 className="text-base font-bold text-slate-900">{deepDiveData.project_name}</h3>
                        <p className="text-xs text-slate-500">{deepDiveData.objective}</p>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {deepDiveData.technologies?.map((t, idx) => (
                          <Badge key={idx} variant="primary" size="xs">
                            {t}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                          <Cpu className="w-3.5 h-3.5 text-slate-600" />
                          <span>Architecture</span>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.architecture}</p>
                      </div>

                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                          <Database className="w-3.5 h-3.5 text-slate-600" />
                          <span>Database Design</span>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.database_choice}</p>
                      </div>

                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                          <Terminal className="w-3.5 h-3.5 text-slate-600" />
                          <span>API Design</span>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.apis_design}</p>
                      </div>

                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                          <Zap className="w-3.5 h-3.5 text-slate-600" />
                          <span>Key Challenge</span>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.challenges_solutions}</p>
                      </div>

                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                          <Shield className="w-3.5 h-3.5 text-slate-600" />
                          <span>Security & Auth</span>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.security_aspects}</p>
                      </div>

                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                          <GitBranch className="w-3.5 h-3.5 text-slate-600" />
                          <span>10x Scale Strategy</span>
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.scalability_notes}</p>
                      </div>
                    </div>
                  </div>

                  {/* Project Interview Questions */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                      Project-Specific Interview Questions ({deepDiveData.interview_questions?.length || 0})
                    </h3>

                    {deepDiveData.interview_questions?.map((q, idx) => (
                      <div key={idx} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1 flex-1">
                            <div className="flex items-center gap-2">
                              <Badge variant={q.difficulty.toLowerCase()} size="xs">{q.difficulty}</Badge>
                              <Badge variant="primary" size="xs">{q.skill}</Badge>
                            </div>
                            <h4 className="text-sm font-bold text-slate-900">{q.question}</h4>
                          </div>

                          <button
                            onClick={() => navigate('/mock-interview', { state: { selectedQuestion: q } })}
                            className="flex items-center gap-1 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-md transition-colors flex-shrink-0"
                          >
                            <Mic className="w-3 h-3 text-slate-600" />
                            <span>Practice</span>
                          </button>
                        </div>

                        <p className="text-xs text-slate-500">
                          <b>Rationale:</b> {q.why_this_question}
                        </p>

                        {q.expected_answer_points && (
                          <div className="pt-2 border-t border-slate-100 text-xs text-slate-600 space-y-1">
                            <span className="font-semibold text-slate-700">Expected Talking Points:</span>
                            <ul className="space-y-0.5 pl-2">
                              {q.expected_answer_points.map((pt, pidx) => (
                                <li key={pidx} className="flex items-start gap-1">
                                  <span className="text-blue-500 font-bold">•</span>
                                  <span>{pt}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </>
          )}
        </div>
      )}
    </div>
  );
};
