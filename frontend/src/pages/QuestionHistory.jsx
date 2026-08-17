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
  ShieldCheck,
  Copy,
  Check,
  ArrowRight,
  Sparkles,
  RotateCcw,
  Award,
  Target,
  BarChart3,
  Calendar,
  Layers,
  Filter
} from 'lucide-react';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';

export const QuestionHistory = () => {
  const navigate = useNavigate();
  const { currentSessionId, clearSessionHistory, autoClearOnClose, setAutoClearOnClose, showToast } = useSession();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  // Filters and Sorting
  const [selectedDifficulty, setSelectedDifficulty] = useState('ALL');
  const [selectedScoreFilter, setSelectedScoreFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('newest'); // 'newest', 'oldest', 'highest', 'lowest'

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

  const handleCopyModelAnswer = (text, id) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
    showToast('Suggested model answer copied to clipboard.');
  };

  const handleReattempt = (item, idx) => {
    navigate('/mock-interview', {
      state: {
        freshAttempt: true,
        selectedQuestion: {
          id: item.question_id || item.id || `q-history-${idx}`,
          instance_id: `reattempt_${Date.now()}_${idx}_${Math.random().toString(36).substring(2, 7)}`,
          is_reattempt: true,
          question: item.question_text || 'Technical Question',
          skill: item.skill || 'Technical',
          difficulty: item.difficulty || 'Medium',
          question_type: item.question_type || 'Technical',
          based_on: item.based_on || `Skill: ${item.skill || 'Technical'}`,
          why_this_question: item.why_this_question || `Assesses hands-on proficiency with ${item.skill || 'technical domains'}.`,
          expected_answer_points: item.expected_points || item.expected_answer_points || [],
          sample_answer: item.improved_answer || item.sample_answer || '',
        },
      },
    });
  };

  const handlePracticeFollowUp = (item) => {
    if (!item.follow_up_question) return;
    navigate('/mock-interview', {
      state: {
        selectedQuestion: {
          id: `followup-${Date.now()}`,
          question: item.follow_up_question,
          skill: item.skill || 'Technical Depth',
          difficulty: item.next_recommended_difficulty || item.difficulty || 'Hard',
          question_type: 'Technical Follow-Up',
          based_on: `Follow-up to: ${item.question_text ? item.question_text.slice(0, 45) + '...' : 'Previous Attempt'}`,
          why_this_question: 'Assesses follow-up problem solving and architectural depth under live pressure.',
          expected_answer_points: item.concepts_missed || ['Core solution architecture', 'Performance trade-offs', 'Scalability'],
          sample_answer: item.improved_answer || '',
        },
      },
    });
  };

  // Aggregated Stats
  const totalCount = history.length;
  const avgScore = totalCount > 0
    ? Math.round(
        history.reduce((sum, item) => sum + (typeof item.overall_score === 'number' ? item.overall_score : (item.score ?? 0)), 0) / totalCount
      )
    : 0;
  const strongCount = history.filter((item) => {
    const s = typeof item.overall_score === 'number' ? item.overall_score : (item.score ?? 0);
    return s >= 70;
  }).length;
  const growthCount = totalCount - strongCount;

  // Filtered & Sorted History
  const filteredHistory = history
    .filter((item) => {
      const s = typeof item.overall_score === 'number' ? item.overall_score : (item.score ?? 0);
      if (selectedDifficulty !== 'ALL' && item.difficulty?.toLowerCase() !== selectedDifficulty.toLowerCase()) {
        return false;
      }
      if (selectedScoreFilter === 'STRONG' && s < 70) return false;
      if (selectedScoreFilter === 'GROWTH' && s >= 70) return false;
      return true;
    })
    .sort((a, b) => {
      const scoreA = typeof a.overall_score === 'number' ? a.overall_score : (a.score ?? 0);
      const scoreB = typeof b.overall_score === 'number' ? b.overall_score : (b.score ?? 0);
      if (sortBy === 'highest') return scoreB - scoreA;
      if (sortBy === 'lowest') return scoreA - scoreB;
      if (sortBy === 'oldest') {
        const dateA = a.evaluated_at ? new Date(a.evaluated_at).getTime() : 0;
        const dateB = b.evaluated_at ? new Date(b.evaluated_at).getTime() : 0;
        return dateA - dateB;
      }
      // default: newest
      const dateA = a.evaluated_at ? new Date(a.evaluated_at).getTime() : 0;
      const dateB = b.evaluated_at ? new Date(b.evaluated_at).getTime() : 0;
      return dateB - dateA;
    });

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Question History</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Review previous mock interview answers with full 6-axis criteria evaluations and model answers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/mock-interview')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm"
          >
            <Mic className="w-3.5 h-3.5" />
            <span>Mock Interview Practice</span>
          </button>

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
      </div>

      {/* Session Privacy & Retention Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0" />
          <span>
            <b>{autoClearOnClose ? '🔒 Ephemeral Privacy Mode:' : '💾 Persistent History Mode:'}</b>{' '}
            {autoClearOnClose
              ? 'Interview attempts and evaluations are automatically purged when you close the browser window.'
              : 'Interview attempts stay saved in local database across browser restarts until cleared.'}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[11px] font-semibold text-slate-500">Auto-clear on close:</span>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={autoClearOnClose}
              onChange={(e) => setAutoClearOnClose(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-8 h-4.5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3.5 after:w-3.5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </div>

      {/* Summary Stats Overview Bar */}
      {totalCount > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 bg-white border border-slate-200 rounded-xl shadow-xs text-center space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Attempted</span>
            <div className="text-lg font-bold text-slate-900">{totalCount} Questions</div>
          </div>
          <div className="p-3.5 bg-white border border-slate-200 rounded-xl shadow-xs text-center space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Average Score</span>
            <div className="text-lg font-bold text-slate-900">{avgScore}%</div>
          </div>
          <div className="p-3.5 bg-white border border-slate-200 rounded-xl shadow-xs text-center space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-600">Strong (≥70%)</span>
            <div className="text-lg font-bold text-emerald-700">{strongCount} Answers</div>
          </div>
          <div className="p-3.5 bg-white border border-slate-200 rounded-xl shadow-xs text-center space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-600">Growth Areas (&lt;70%)</span>
            <div className="text-lg font-bold text-amber-700">{growthCount} Answers</div>
          </div>
        </div>
      )}

      {/* Filter & Sort Controls */}
      {totalCount > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 text-slate-600 font-medium">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span>Difficulty:</span>
            </div>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-md px-2 py-1 text-slate-700 font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="ALL">All Difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
              <option value="Expert">Expert</option>
            </select>

            <div className="flex items-center gap-1.5 text-slate-600 font-medium ml-2">
              <span>Score Tier:</span>
            </div>
            <select
              value={selectedScoreFilter}
              onChange={(e) => setSelectedScoreFilter(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-md px-2 py-1 text-slate-700 font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="ALL">All Scores</option>
              <option value="STRONG">Strong Answers (≥70%)</option>
              <option value="GROWTH">Growth Needed (&lt;70%)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500 font-medium">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-md px-2 py-1 text-slate-700 font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="highest">Highest Score</option>
              <option value="lowest">Lowest Score</option>
            </select>
          </div>
        </div>
      )}

      {/* History List */}
      <div className="space-y-6">
        {loading ? (
          <div className="p-12 bg-white rounded-xl border border-slate-200 text-center space-y-2">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-slate-500">Loading your question history & evaluations...</p>
          </div>
        ) : filteredHistory.length > 0 ? (
          filteredHistory.map((item, idx) => {
            const score = typeof item.overall_score === 'number' ? item.overall_score : (item.score ?? 0);
            const verdictText =
              item.verdict_rating ||
              item.verdict ||
              (score >= 85
                ? 'Exceptional'
                : score >= 70
                ? 'Strong Technical Answer'
                : score >= 50
                ? 'Adequate with Gaps'
                : score > 0
                ? 'Needs Technical Depth'
                : 'No Answer Provided');

            const verdictVariant =
              score >= 75 ? 'success' : score >= 50 ? 'warning' : 'danger';

            const wordCount = item.user_answer?.trim()
              ? item.user_answer.trim().split(/\s+/).filter(Boolean).length
              : 0;

            const itemId = item.id || item._id || `history-${idx}`;

            // Model answer formatting fallback
            let modelAnswerText = item.improved_answer || item.sample_answer;
            if (
              !modelAnswerText ||
              modelAnswerText.toLowerCase().startsWith('to answer effectively') ||
              modelAnswerText.toLowerCase().startsWith('a strong answer should')
            ) {
              modelAnswerText = `In our project architecture, we implemented ${item.skill || 'this technology'} to handle core data processing with high reliability. We established clear architectural boundaries, optimized data validation and query execution, and handled edge cases defensively. This approach provided resilient throughput, minimal processing overhead, and predictable sub-50ms latency in production.`;
            }

            // Sub-scores
            const relevanceScore = item.relevance_score ?? item.axis_scores?.relevance ?? (score > 0 ? score : 0);
            const technicalScore = item.technical_accuracy_score ?? item.axis_scores?.technical ?? (score > 0 ? score : 0);
            const completenessScore = item.completeness_score ?? item.axis_scores?.completeness ?? (score > 0 ? score : 0);
            const clarityScore = item.clarity_score ?? item.axis_scores?.clarity ?? (score > 0 ? score : 0);
            const confidenceScore = item.confidence_score ?? item.axis_scores?.confidence ?? (score > 0 ? score : 0);
            const communicationScore = item.communication_score ?? item.axis_scores?.communication ?? (score > 0 ? score : 0);

            // Growth items
            const growthItems =
              item.concepts_missed && item.concepts_missed.length > 0
                ? item.concepts_missed
                : item.weaknesses && item.weaknesses.length > 0
                ? item.weaknesses
                : [
                    `Explain concrete system mechanisms and practical trade-offs for ${item.skill || 'this topic'}.`,
                    'Incorporate quantifiable impact metrics (latency, throughput, memory overhead).',
                  ];

            // Strengths items
            const strengthsItems =
              item.strengths && item.strengths.length > 0
                ? item.strengths
                : score > 0
                ? ['Demonstrated foundational understanding of the core concept.']
                : ['No technical response was submitted.'];

            return (
              <div
                key={itemId}
                className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4 transition-all"
              >
                {/* Header: Question Meta & Title */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3 border-b border-slate-100">
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                        #{idx + 1}
                      </span>
                      <Badge variant={item.difficulty?.toLowerCase() || 'medium'} size="xs">
                        {item.difficulty || 'Medium'}
                      </Badge>
                      <Badge variant="primary" size="xs">
                        {item.skill || 'Technical'}
                      </Badge>
                      {item.question_type && (
                        <Badge variant="default" size="xs">
                          {item.question_type}
                        </Badge>
                      )}
                      {item.based_on && (
                        <span className="text-[11px] text-slate-500 ml-1">
                          Based on: <span className="font-semibold text-slate-700">{item.based_on}</span>
                        </span>
                      )}
                    </div>
                    <h3 className="text-base font-bold text-slate-900 leading-snug">
                      {item.question_text || 'Interview Question'}
                    </h3>
                  </div>

                  {item.evaluated_at && (
                    <div className="flex items-center gap-1 text-[11px] text-slate-400 shrink-0">
                      <Calendar className="w-3 h-3" />
                      <span>
                        {new Date(item.evaluated_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                    </div>
                  )}
                </div>

                {/* Candidate Submitted Answer */}
                <div className="p-3.5 bg-slate-50/80 rounded-xl border border-slate-200/80 space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                    <span>Your Submitted Answer:</span>
                    <span className="font-normal lowercase text-slate-400">{wordCount} words</span>
                  </div>
                  <p className="text-xs text-slate-800 whitespace-pre-wrap leading-relaxed">
                    "{item.user_answer || 'No answer recording available.'}"
                  </p>
                </div>

                {/* Main 6-Axis Evaluation Block - Exactly Matching Mock Interview */}
                <div className="bg-slate-50/50 border border-slate-200/90 rounded-xl p-4 sm:p-5 space-y-4">
                  {/* Score & Verdict Header */}
                  <div className="flex flex-col sm:flex-row items-center gap-5 pb-4 border-b border-slate-200/70">
                    <ScoreRing score={score} size={88} strokeWidth={7} label="Answer Score" />
                    <div className="space-y-1.5 flex-1 text-center sm:text-left">
                      <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                        <h4 className="text-base font-bold text-slate-900">Answer Evaluation</h4>
                        <Badge variant={verdictVariant}>{verdictText}</Badge>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed font-normal">
                        {item.feedback_summary ||
                          item.rationale ||
                          (score >= 75
                            ? 'Strong technical foundation with clear domain reasoning.'
                            : score > 0
                            ? 'Adequate answer with areas for deeper architectural rigor.'
                            : 'No valid technical answer was detected (0/100). Review the benchmark model response below.')}
                      </p>
                    </div>
                  </div>

                  {/* 6-Axis Sub-Scores Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                    {[
                      { label: 'Relevance', val: relevanceScore },
                      { label: 'Technical Depth', val: technicalScore },
                      { label: 'Completeness', val: completenessScore },
                      { label: 'Clarity', val: clarityScore },
                      { label: 'Confidence', val: confidenceScore },
                      { label: 'Communication', val: communicationScore },
                    ].map((axis, aIdx) => (
                      <div
                        key={aIdx}
                        className="p-2.5 bg-white rounded-lg border border-slate-200/70 text-center shadow-2xs"
                      >
                        <div className="text-[11px] text-slate-500 font-medium">{axis.label}</div>
                        <div className="text-sm font-bold text-slate-800 mt-0.5">{axis.val}/100</div>
                      </div>
                    ))}
                  </div>

                  {/* Strengths & Missed Concepts Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                    {/* Strengths */}
                    <div className="p-3.5 bg-emerald-50/40 rounded-lg border border-emerald-100 space-y-2">
                      <div className="flex items-center gap-1.5 text-emerald-800 font-bold text-xs">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Answer Strengths</span>
                      </div>
                      <ul className="space-y-1.5">
                        {strengthsItems.map((s, sidx) => (
                          <li key={sidx} className="flex items-start gap-1.5 text-xs text-slate-700">
                            <span className="text-emerald-500 font-bold">•</span>
                            <span className="leading-relaxed">{s}</span>
                          </li>
                        ))}
                      </ul>

                      {/* Concepts Covered Tags */}
                      {item.concepts_covered && item.concepts_covered.length > 0 && (
                        <div className="pt-2 border-t border-emerald-200/60">
                          <span className="text-[11px] font-bold text-emerald-800 block mb-1">
                            Concepts Covered:
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {item.concepts_covered.map((c, cIdx) => (
                              <span
                                key={cIdx}
                                className="inline-flex items-center bg-white px-2 py-0.5 rounded text-[11px] font-medium text-emerald-800 border border-emerald-200"
                              >
                                ✓ {c}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Missed Concepts / Growth Areas */}
                    <div className="p-3.5 bg-amber-50/40 rounded-lg border border-amber-100 space-y-2">
                      <div className="flex items-center gap-1.5 text-amber-800 font-bold text-xs">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                        <span>Missed Concepts / Growth</span>
                      </div>
                      <ul className="space-y-1.5">
                        {growthItems.map((w, widx) => (
                          <li key={widx} className="flex items-start gap-1.5 text-xs text-slate-700">
                            <span className="text-amber-500 font-bold">•</span>
                            <span className="leading-relaxed">{w}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* STAR Method Assessment (if present) */}
                  {item.star_feedback && (
                    <div className="p-3.5 bg-white rounded-lg border border-slate-200/80 space-y-2">
                      <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wide block">
                        STAR Framework Analysis:
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-xs">
                        {Object.entries(item.star_feedback).map(([key, val], sIdx) => (
                          <div key={sIdx} className="p-2 bg-slate-50 rounded border border-slate-100 space-y-0.5">
                            <span className="font-bold text-slate-800 uppercase text-[10px]">{key}:</span>
                            <p className="text-slate-600 text-[11px] leading-snug">{val}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Model Answer (Suggested Ideal Interview Response) */}
                  <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-3 shadow-2xs">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 uppercase tracking-wide flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        Suggested Model Answer (Ideal Interview Response):
                      </span>
                      <button
                        onClick={() => handleCopyModelAnswer(modelAnswerText, itemId)}
                        className="flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200 transition-colors shadow-2xs"
                      >
                        {copiedId === itemId ? (
                          <Check className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                        <span>{copiedId === itemId ? 'Copied' : 'Copy Answer'}</span>
                      </button>
                    </div>

                    <div className="text-xs text-slate-800 leading-relaxed bg-slate-50/60 p-3.5 rounded-lg border border-slate-200/80 font-normal">
                      {modelAnswerText}
                    </div>

                    {/* Interviewer Checkpoints */}
                    {(item.expected_points || item.expected_answer_points) &&
                      (item.expected_points || item.expected_answer_points).length > 0 && (
                        <div className="text-[11px] text-slate-600 bg-slate-100/70 p-2.5 rounded-md border border-slate-200/60 flex flex-wrap items-center gap-1.5">
                          <span className="font-semibold text-slate-800 mr-1">Interviewer Checkpoints:</span>
                          {(item.expected_points || item.expected_answer_points).map((pt, pIdx) => (
                            <span
                              key={pIdx}
                              className="inline-flex items-center bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-700 text-[10px]"
                            >
                              {pt}
                            </span>
                          ))}
                        </div>
                      )}
                  </div>

                  {/* Follow-up Question Prompt */}
                  {item.follow_up_question && (
                    <div className="p-3 bg-blue-50/60 border border-blue-200/80 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                      <div className="space-y-0.5">
                        <span className="text-[11px] font-bold text-blue-900 uppercase tracking-wide flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-blue-600" />
                          Adaptive Follow-Up Question:
                        </span>
                        <p className="text-xs text-slate-800 font-medium">"{item.follow_up_question}"</p>
                      </div>
                      <button
                        onClick={() => handlePracticeFollowUp(item)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors whitespace-nowrap"
                      >
                        <span>Practice Follow-Up</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  )}

                  {/* Card Bottom Actions */}
                  <div className="flex items-center justify-end gap-2 pt-1">
                    <button
                      onClick={() => handleReattempt(item, idx)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-lg transition-colors border border-slate-200/70"
                    >
                      <RotateCcw className="w-3.5 h-3.5 text-slate-600" />
                      <span>Re-attempt in Mock Interview</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="p-12 bg-white rounded-xl border border-slate-200 text-center space-y-3">
            <History className="w-10 h-10 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-800">
              {history.length > 0 ? 'No attempts match current filters' : 'No mock interview attempts yet'}
            </h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              {history.length > 0
                ? 'Try adjusting your difficulty or score filter options above to see previous question attempts.'
                : 'Practice technical questions with voice dictation or typing in Mock Interview to generate your 6-axis performance history.'}
            </p>
            {history.length > 0 ? (
              <button
                onClick={() => {
                  setSelectedDifficulty('ALL');
                  setSelectedScoreFilter('ALL');
                }}
                className="mt-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
              >
                <span>Reset Filters</span>
              </button>
            ) : (
              <button
                onClick={() => navigate('/mock-interview')}
                className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
              >
                <Mic className="w-3.5 h-3.5" />
                <span>Start Mock Interview</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Clear Confirmation Modal */}
      <Modal
        isOpen={isClearModalOpen}
        onClose={() => setIsClearModalOpen(false)}
        title="Clear Interview History?"
        maxWidth="max-w-md"
      >
        <div className="space-y-4 text-xs text-slate-600">
          <p>
            Are you sure you want to clear all mock interview attempts and evaluations recorded in this session? This action cannot be undone.
          </p>
          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={() => setIsClearModalOpen(false)}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleClearHistory}
              disabled={clearing}
              className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors"
            >
              {clearing ? 'Clearing...' : 'Yes, Clear All'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
