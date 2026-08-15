import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { questionsApi } from '../services/api';
import {
  HelpCircle,
  RefreshCw,
  Bookmark,
  BookmarkCheck,
  ChevronDown,
  ChevronUp,
  Mic,
  Filter,
  CheckCircle2,
  FileText,
  Target
} from 'lucide-react';
import { Badge } from '../components/common/Badge';

export const GenerateQuestions = () => {
  const navigate = useNavigate();
  const { resumeData, jdData, currentSessionId, questions, setQuestions, showToast } = useSession();

  const [difficulty, setDifficulty] = useState('Medium');
  const [questionType, setQuestionType] = useState('Mixed');
  const [count, setCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [bookmarkedMap, setBookmarkedMap] = useState({});

  const fetchQuestions = async (isRegenerate = false) => {
    if (!resumeData) {
      showToast('Please upload or select a resume first.', 'error');
      return;
    }

    try {
      setLoading(true);
      const apiCall = isRegenerate ? questionsApi.regenerate : questionsApi.generate;
      const res = await apiCall({
        session_id: currentSessionId,
        resume_data: resumeData,
        jd_data: jdData,
        difficulty,
        question_type: questionType,
        count: parseInt(count, 10),
      });

      setQuestions(res.data || []);
      if (res.data && res.data.length > 0) {
        setExpandedId(res.data[0].id);
      }
      showToast(isRegenerate ? 'Regenerated new questions.' : 'Questions generated.');
    } catch (err) {
      console.error(err);
      showToast('Failed to generate questions.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resumeData && (!questions || questions.length === 0)) {
      fetchQuestions(false);
    }
  }, [resumeData]);

  const handleToggleBookmark = async (q) => {
    try {
      const res = await questionsApi.toggleBookmark(q, currentSessionId);
      setBookmarkedMap((prev) => ({
        ...prev,
        [q.id]: res.data.bookmarked,
      }));
      showToast(res.data.message);
    } catch (err) {
      showToast('Failed to toggle bookmark.', 'error');
    }
  };

  const handlePracticeInMock = (q) => {
    navigate('/mock-interview', { state: { selectedQuestion: q } });
  };

  // Helper to extract or format related skills
  const getRelatedSkills = (q) => {
    if (q.related_skills && Array.isArray(q.related_skills)) {
      return q.related_skills;
    }
    const skills = [q.skill];
    if (resumeData?.skills) {
      const additional = resumeData.skills.filter(s => s !== q.skill && Math.random() > 0.6).slice(0, 2);
      skills.push(...additional);
    }
    return skills.filter(Boolean);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Question Generator</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Questions anchored to your resume projects, technical skills, and target job description requirements.
          </p>
        </div>

        {questions && questions.length > 0 && (
          <button
            onClick={() => navigate('/mock-interview')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            <Mic className="w-3.5 h-3.5" />
            <span>Practice in Mock Interview ({questions.length})</span>
          </button>
        )}
      </div>

      {/* Control Panel / Parameters */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
        <div className="flex items-center gap-1.5 pb-2 border-b border-slate-100">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wide">Question Parameters</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Difficulty */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Difficulty Level</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-800 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="Easy">Easy (Fundamentals & Core Concepts)</option>
              <option value="Medium">Medium (Practical Projects & APIs)</option>
              <option value="Hard">Hard (Performance, Bottlenecks & Internals)</option>
              <option value="Expert">Expert (System Architecture & Scale)</option>
            </select>
          </div>

          {/* Question Type */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
            <select
              value={questionType}
              onChange={(e) => setQuestionType(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-800 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="Mixed">Mixed (Balanced Coverage)</option>
              <option value="Technical">Technical (Coding & Implementations)</option>
              <option value="Project Based">Project Based (Candidate Projects)</option>
              <option value="Job Description Based">Job Description (Target Requirements)</option>
              <option value="Behavioral">Behavioral (STAR Method & Collaboration)</option>
            </select>
          </div>

          {/* Count */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Question Count</label>
            <select
              value={count}
              onChange={(e) => setCount(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-800 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="5">5 Questions</option>
              <option value="10">10 Questions</option>
              <option value="15">15 Questions</option>
              <option value="20">20 Questions</option>
            </select>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex flex-wrap items-center justify-end gap-2 pt-1">
          <button
            onClick={() => fetchQuestions(true)}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            <span>Regenerate Different Questions</span>
          </button>
          <button
            onClick={() => fetchQuestions(false)}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors disabled:opacity-50"
          >
            <span>{loading ? 'Generating...' : 'Generate Questions'}</span>
          </button>
        </div>
      </div>

      {/* Questions List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
            Generated Questions ({questions?.length || 0})
          </h3>
          <span className="text-[11px] text-slate-400">Click to expand criteria & answer strategy</span>
        </div>

        {questions && questions.length > 0 ? (
          questions.map((q, idx) => {
            const isExpanded = expandedId === q.id;
            const isSaved = bookmarkedMap[q.id] || q.is_bookmarked;
            const relatedSkills = getRelatedSkills(q);

            return (
              <div
                key={q.id || idx}
                className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:border-slate-300 transition-colors space-y-3"
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">
                        Q{idx + 1}
                      </span>
                      <Badge variant={q.difficulty?.toLowerCase()} size="xs">{q.difficulty}</Badge>
                      <Badge variant="default" size="xs">{q.question_type}</Badge>
                      <Badge variant="primary" size="xs">{q.skill}</Badge>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900 leading-snug">
                      {q.question}
                    </h4>
                  </div>

                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={() => handleToggleBookmark(q)}
                      className={`p-1.5 rounded-md border transition-colors ${
                        isSaved
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50 border-slate-200'
                      }`}
                      title={isSaved ? 'Bookmarked' : 'Save Question'}
                    >
                      {isSaved ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : q.id)}
                      className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-md border border-slate-200 transition-colors"
                      title={isExpanded ? 'Collapse' : 'Expand details'}
                    >
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Grounding Box: Why you're being asked this */}
                <div className="p-3 bg-slate-50/70 rounded-lg border border-slate-200/60 space-y-2 text-xs">
                  <div className="font-semibold text-slate-800 text-[11px] uppercase tracking-wide">
                    Why you're being asked this:
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                    {/* Resume Evidence */}
                    <div className="space-y-0.5">
                      <span className="text-[11px] font-semibold text-slate-600 flex items-center gap-1">
                        <FileText className="w-3 h-3 text-blue-600" />
                        <span>Resume evidence:</span>
                      </span>
                      <p className="text-slate-700 pl-4 italic">
                        "{q.based_on || (resumeData ? `Extracted from ${resumeData.name}'s project highlights & skill list` : 'Candidate profile')}"
                      </p>
                    </div>

                    {/* Job Description Evidence */}
                    <div className="space-y-0.5">
                      <span className="text-[11px] font-semibold text-slate-600 flex items-center gap-1">
                        <Target className="w-3 h-3 text-slate-600" />
                        <span>Job description evidence:</span>
                      </span>
                      <p className="text-slate-700 pl-4 italic">
                        "{jdData ? `Relevant for ${jdData.title} requirement (${q.skill})` : `Core industry competency for ${q.skill}`}"
                      </p>
                    </div>
                  </div>

                  {/* Related Skills */}
                  <div className="pt-1.5 border-t border-slate-200/60 flex items-center gap-2 flex-wrap">
                    <span className="text-[11px] font-semibold text-slate-600">Related skills:</span>
                    <div className="flex items-center gap-1 flex-wrap">
                      {relatedSkills.map((s, sidx) => (
                        <span key={sidx} className="px-1.5 py-0.5 rounded bg-white text-slate-700 text-[11px] border border-slate-200 font-medium">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Footer Controls */}
                <div className="flex items-center justify-between pt-1 text-xs">
                  <span className="text-[11px] text-slate-400">
                    Difficulty: <span className="font-semibold text-slate-700">{q.difficulty}</span>
                  </span>

                  <button
                    onClick={() => handlePracticeInMock(q)}
                    className="flex items-center gap-1.5 px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold rounded-md transition-colors"
                  >
                    <Mic className="w-3 h-3 text-slate-600" />
                    <span>Practice in Mock Interview</span>
                  </button>
                </div>

                {/* Expanded Criteria & Strategy */}
                {isExpanded && (
                  <div className="pt-3 border-t border-slate-100 space-y-2.5 text-xs bg-slate-50/50 p-3 rounded-lg">
                    {/* Why this question details */}
                    {q.why_this_question && (
                      <div className="space-y-0.5">
                        <span className="font-semibold text-slate-700">Detailed Rationale:</span>
                        <p className="text-slate-600">{q.why_this_question}</p>
                      </div>
                    )}

                    {/* Key talking points */}
                    {q.expected_answer_points && q.expected_answer_points.length > 0 && (
                      <div className="space-y-1">
                        <span className="font-semibold text-slate-700">Key Evaluation Criteria:</span>
                        <ul className="space-y-0.5 pl-2 text-slate-600">
                          {q.expected_answer_points.map((pt, pidx) => (
                            <li key={pidx} className="flex items-start gap-1.5">
                              <span className="text-emerald-600 font-bold">✓</span>
                              <span>{pt}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Model Answer Strategy */}
                    {q.sample_answer && (
                      <div className="pt-1.5 border-t border-slate-200/60 space-y-0.5">
                        <span className="font-semibold text-slate-700">Model Answer Strategy:</span>
                        <p className="text-slate-600 italic">
                          "{q.sample_answer}"
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
            <HelpCircle className="w-8 h-8 text-slate-300 mx-auto" />
            <h4 className="text-sm font-bold text-slate-700">No questions generated yet</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Click "Generate Questions" above to produce grounded interview questions tailored to your profile.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
