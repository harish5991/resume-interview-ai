import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { jobApi, matchApi } from '../services/api';
import {
  Target,
  Search,
  Check,
  X,
  ArrowRight,
  Layers,
  CheckCircle2
} from 'lucide-react';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';

export const JobMatch = () => {
  const navigate = useNavigate();
  const { resumeData, jdData, setJdData, matchData, setMatchData, showToast } = useSession();
  const [jdText, setJdText] = useState(jdData?.raw_text || '');
  const [analyzing, setAnalyzing] = useState(false);
  const [samples, setSamples] = useState([]);

  useEffect(() => {
    jobApi.getSamples().then((res) => setSamples(res.data)).catch(() => {});
  }, []);

  const handleAnalyzeJd = async (e) => {
    e.preventDefault();
    if (!jdText.trim()) return;

    try {
      setAnalyzing(true);
      showToast('Analyzing Job Description...', 'info');
      const res = await jobApi.analyze(jdText);
      await setJdData(res.data);
      if (resumeData) {
        const matchRes = await matchApi.match(resumeData, res.data);
        setMatchData(matchRes.data);
      }
      showToast('Job Description analyzed and matched.');
    } catch (err) {
      console.error(err);
      showToast(err.response?.data?.detail || 'Failed to analyze Job Description.', 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSelectSample = async (sample) => {
    setJdText(sample.raw_text);
    await setJdData(sample);
    if (resumeData) {
      const matchRes = await matchApi.match(resumeData, sample);
      setMatchData(matchRes.data);
    }
    showToast(`Loaded sample role: ${sample.title}`);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Job Match Analysis</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Compare resume competencies against target job requirements to reveal matching vs missing skills.
          </p>
        </div>

        {matchData && (
          <button
            onClick={() => navigate('/questions')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors"
          >
            <span>Generate Grounded Questions</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Input & Sample Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Paste JD Box */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">Target Job Description</h3>
            <span className="text-[11px] text-slate-400">Paste job requirements & tech stack</span>
          </div>

          <form onSubmit={handleAnalyzeJd} className="space-y-3">
            <textarea
              rows={6}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste Job Description here (e.g. Seeking a Full Stack Engineer with Python, React, and PostgreSQL experience...)"
              className="w-full text-xs font-mono p-3 border border-slate-200 rounded-lg focus:ring-1 focus:ring-blue-500 focus:outline-none bg-slate-50/50"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={analyzing || !jdText.trim()}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50"
              >
                <Search className="w-3.5 h-3.5" />
                <span>{analyzing ? 'Analyzing Match...' : 'Calculate Job Match'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Sample Roles */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
          <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wide">
            Sample Job Descriptions
          </div>
          <p className="text-[11px] text-slate-500">Pick a sample position to test semantic matching:</p>

          <div className="space-y-1.5 pt-1">
            {samples.map((s) => (
              <button
                key={s.id}
                onClick={() => handleSelectSample(s)}
                className={`w-full text-left p-2 rounded-lg border text-xs transition-colors ${
                  jdData?.title === s.title
                    ? 'border-blue-500 bg-blue-50/50 font-semibold text-blue-900'
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700'
                }`}
              >
                <div className="font-semibold text-slate-900">{s.title}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">{s.company || 'Tech Corp'} • {s.experience_years}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Match Results & Grounding */}
      {matchData ? (
        <div className="space-y-4">
          {/* Main Match Summary Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex flex-col sm:flex-row items-center gap-6 pb-5 border-b border-slate-100">
              <ScoreRing score={matchData.match_percentage} size={88} strokeWidth={7} label="Job Match" />
              <div className="space-y-1.5 flex-1 text-center sm:text-left">
                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                  <h3 className="text-base font-bold text-slate-900">
                    Match Analysis: {jdData?.title || 'Target Role'}
                  </h3>
                  <Badge variant={matchData.match_percentage >= 75 ? 'success' : 'warning'}>
                    {matchData.match_percentage >= 75 ? 'Strong Role Alignment' : 'Moderate Alignment'}
                  </Badge>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
                  {matchData.match_summary}
                </p>
                <div className="text-[11px] text-slate-500 pt-0.5">
                  <b>Scoring Logic:</b> {matchData.relevance_explanation}
                </div>
              </div>
            </div>

            {/* Skills Match vs Missing */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
              {/* Matching Skills */}
              <div className="p-3.5 bg-emerald-50/40 rounded-lg border border-emerald-100 space-y-2">
                <div className="flex items-center gap-1.5 text-emerald-800 font-bold text-xs">
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Matching Skills ({matchData.matching_skills?.length || 0})</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {matchData.matching_skills?.map((s, idx) => (
                    <Badge key={idx} variant="success" size="xs">
                      {s}
                    </Badge>
                  ))}
                  {matchData.matching_skills?.length === 0 && (
                    <span className="text-xs text-slate-500">No direct skill matches detected.</span>
                  )}
                </div>
              </div>

              {/* Missing Skills */}
              <div className="p-3.5 bg-rose-50/40 rounded-lg border border-rose-100 space-y-2">
                <div className="flex items-center gap-1.5 text-rose-800 font-bold text-xs">
                  <X className="w-3.5 h-3.5 text-rose-600" />
                  <span>Missing Target Skills ({matchData.missing_skills?.length || 0})</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {matchData.missing_skills?.map((s, idx) => (
                    <Badge key={idx} variant="danger" size="xs">
                      {s}
                    </Badge>
                  ))}
                  {matchData.missing_skills?.length === 0 && (
                    <span className="text-xs text-slate-500">Full skill overlap across all requirements.</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Relevant Projects & Recommendations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-2.5">
              <div className="flex items-center gap-1.5 text-slate-800 font-bold text-xs uppercase tracking-wide">
                <Layers className="w-3.5 h-3.5 text-slate-600" />
                <span>Most Relevant Resume Projects</span>
              </div>
              <ul className="space-y-2">
                {matchData.relevant_projects?.map((rp, idx) => (
                  <li key={idx} className="p-2.5 bg-slate-50 rounded-lg text-xs text-slate-700 border border-slate-100 flex items-start gap-2">
                    <span className="text-blue-500 font-bold">•</span>
                    <span>{rp}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-2.5">
              <div className="flex items-center gap-1.5 text-slate-800 font-bold text-xs uppercase tracking-wide">
                <CheckCircle2 className="w-3.5 h-3.5 text-slate-600" />
                <span>Preparation Recommendations</span>
              </div>
              <ul className="space-y-2">
                {matchData.recommendations?.map((rec, idx) => (
                  <li key={idx} className="p-2.5 bg-slate-50 rounded-lg text-xs text-slate-700 border border-slate-100 flex items-start gap-2">
                    <span className="text-amber-500 font-bold">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
          <Target className="w-8 h-8 text-slate-300 mx-auto" />
          <h4 className="text-sm font-bold text-slate-700">No job match calculated</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Paste a job description or choose a sample role above to see semantic overlap and missing skills.
          </p>
        </div>
      )}
    </div>
  );
};
