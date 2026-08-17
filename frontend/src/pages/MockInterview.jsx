import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { questionsApi, interviewApi, reportApi } from '../services/api';
import {
  Mic,
  MicOff,
  Send,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Copy,
  Check,
  PlusCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Award,
  Trophy,
  BarChart3,
  FileText,
  RotateCcw,
  Sparkles,
  Download,
  BookOpen,
  ArrowLeft,
  CheckCircle,
  Flame,
  Target
} from 'lucide-react';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';

const getQuestionKey = (q, idx) => {
  if (!q) return `q_idx_${idx}`;
  return q.instance_id || q.question_attempt_id || (q.id ? `${q.id}` : `q_idx_${idx}`);
};

export const MockInterview = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { resumeData, jdData, currentSessionId, questions, setQuestions, showToast } = useSession();
  const activeAttemptIdRef = useRef(null);

  // Restore mock interview progress from sessionStorage if browser was refreshed
  const initialProgress = (() => {
    try {
      if (!currentSessionId || !resumeData) return null;
      const raw = sessionStorage.getItem(`mock_interview_progress_${currentSessionId}`);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (parsed.resumeId && parsed.resumeId !== resumeData.id) return null;
      return parsed;
    } catch (e) {
      return null;
    }
  })();

  const targetQ = questions && questions.length > 0 ? questions[initialProgress?.currentIndex || 0] : null;
  const initialKey = targetQ ? getQuestionKey(targetQ, initialProgress?.currentIndex || 0) : null;
  const initialAnswer = (initialKey && initialProgress?.answeredMap?.[initialKey])
    ? initialProgress.answeredMap[initialKey].userAnswer || ''
    : '';
  const initialEval = (initialKey && initialProgress?.answeredMap?.[initialKey])
    ? initialProgress.answeredMap[initialKey].evaluation
    : null;

  const [currentIndex, setCurrentIndex] = useState(initialProgress?.currentIndex || 0);
  const [userAnswer, setUserAnswer] = useState(initialAnswer);
  const [evaluating, setEvaluating] = useState(false);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [evaluation, setEvaluation] = useState(initialEval);
  const [isRecording, setIsRecording] = useState(false);
  const [answeredMap, setAnsweredMap] = useState(initialProgress?.answeredMap || {});
  const [selectedDifficulty, setSelectedDifficulty] = useState(initialProgress?.selectedDifficulty || 'Medium');
  const [isAdaptiveMode, setIsAdaptiveMode] = useState(false);
  const [copiedModel, setCopiedModel] = useState(false);

  // Final Evaluation States
  const [viewMode, setViewMode] = useState(initialProgress?.viewMode || 'interview'); // 'interview' | 'final_evaluation'
  const [finalEvaluation, setFinalEvaluation] = useState(initialProgress?.finalEvaluation || null);
  const [loadingFinalEval, setLoadingFinalEval] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [expandedQuestionIdx, setExpandedQuestionIdx] = useState(null);
  const [copiedSummary, setCopiedSummary] = useState(false);

  // Sync mock interview progress to sessionStorage
  useEffect(() => {
    if (currentSessionId && resumeData) {
      try {
        sessionStorage.setItem(
          `mock_interview_progress_${currentSessionId}`,
          JSON.stringify({
            answeredMap,
            finalEvaluation,
            evaluation,
            currentIndex,
            selectedDifficulty,
            viewMode,
            resumeId: resumeData.id,
          })
        );
      } catch (e) {}
    }
  }, [currentSessionId, resumeData?.id, answeredMap, finalEvaluation, evaluation, currentIndex, selectedDifficulty, viewMode]);

  // Speech Recognition instance
  const [recognition, setRecognition] = useState(null);
  const baseTextRef = useRef('');

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognizer = new SpeechRecognition();
      recognizer.continuous = true;
      recognizer.interimResults = true;
      recognizer.lang = 'en-US';

      recognizer.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = 0; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalTranscript += result[0].transcript + ' ';
          } else {
            interimTranscript += result[0].transcript;
          }
        }

        const sessionTranscript = (finalTranscript + interimTranscript).replace(/\s+/g, ' ').trim();
        const base = baseTextRef.current ? baseTextRef.current.trim() : '';

        if (base && sessionTranscript) {
          setUserAnswer(`${base} ${sessionTranscript}`);
        } else if (sessionTranscript) {
          setUserAnswer(sessionTranscript);
        } else {
          setUserAnswer(base);
        }
      };

      recognizer.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
        showToast(`Speech recognition error: ${event.error}`, 'error');
      };

      recognizer.onend = () => {
        setIsRecording(false);
      };

      setRecognition(recognizer);
    }
  }, []);

  const ensureQuestions = async (targetDiff = selectedDifficulty) => {
    if (!resumeData) return;
    try {
      setLoadingQuestions(true);
      const res = await questionsApi.generate({
        session_id: currentSessionId || 'default',
        resume_data: resumeData,
        jd_data: jdData,
        difficulty: targetDiff,
        question_type: 'Mixed',
        count: 5,
      });

      if (res.data && res.data.length > 0) {
        const enriched = res.data.map((q, idx) => ({
          ...q,
          instance_id: `q_${Date.now()}_${idx}_${Math.random().toString(36).substring(2, 7)}`,
        }));
        setQuestions(enriched);
        setCurrentIndex(0);
        setUserAnswer('');
        setEvaluation(null);
        setAnsweredMap({});
        setFinalEvaluation(null);
        setViewMode('interview');
        showToast(`Loaded ${enriched.length} interview questions.`);
      }
    } catch (err) {
      console.error('Failed to generate questions:', err);
    } finally {
      setLoadingQuestions(false);
    }
  };

  // Track resume ID changes to reset interview state
  const resumeIdRef = useRef(resumeData?.id);
  useEffect(() => {
    if (resumeData && resumeData.id !== resumeIdRef.current) {
      resumeIdRef.current = resumeData.id;
      setCurrentIndex(0);
      setUserAnswer('');
      setEvaluation(null);
      setAnsweredMap({});
      setFinalEvaluation(null);
      setViewMode('interview');
    }
  }, [resumeData?.id]);

  useEffect(() => {
    if (location.state?.selectedQuestion) {
      const q = location.state.selectedQuestion;
      const isReattempt = location.state?.freshAttempt || Boolean(q.is_reattempt);
      const newQ = {
        ...q,
        instance_id: q.instance_id || `q_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      };

      if (questions && questions.length > 0) {
        if (isReattempt) {
          setQuestions([newQ, ...questions]);
          setCurrentIndex(0);
          setUserAnswer('');
          setEvaluation(null);
        } else {
          const foundIdx = questions.findIndex((item) => item.id === q.id || item.question === q.question);
          if (foundIdx !== -1) {
            handleSelectQuestion(foundIdx);
          } else {
            setQuestions([newQ, ...questions]);
            setCurrentIndex(0);
            setUserAnswer('');
            setEvaluation(null);
          }
        }
      } else {
        setQuestions([newQ]);
        setCurrentIndex(0);
        setUserAnswer('');
        setEvaluation(null);
      }
    } else if (resumeData && (!questions || questions.length === 0)) {
      ensureQuestions('Medium');
    }
  }, [resumeData, location.state]);

  const currentQuestion = questions && questions.length > 0 ? questions[currentIndex] : null;
  const totalQuestions = questions?.length || 0;
  const answeredCount = Object.keys(answeredMap).length;
  const isAllAnswered = totalQuestions > 0 && answeredCount >= totalQuestions;
  const wordCount = userAnswer.trim() ? userAnswer.trim().split(/\s+/).length : 0;

  const handleSelectQuestion = (index) => {
    if (index < 0 || index >= (questions?.length || 0)) return;
    if (isRecording && recognition) {
      recognition.stop();
      setIsRecording(false);
    }
    baseTextRef.current = '';
    activeAttemptIdRef.current = null;
    setEvaluating(false);
    setCurrentIndex(index);
    const targetQ = questions[index];
    const targetKey = getQuestionKey(targetQ, index);
    if (targetQ && answeredMap[targetKey]) {
      setEvaluation(answeredMap[targetKey].evaluation);
      setUserAnswer(answeredMap[targetKey].userAnswer || '');
    } else {
      setEvaluation(null);
      setUserAnswer('');
    }
  };

  const toggleRecording = () => {
    if (!recognition) {
      showToast('Speech recognition is not supported in this browser.', 'warning');
      return;
    }

    if (isRecording) {
      recognition.stop();
      setIsRecording(false);
      baseTextRef.current = '';
      showToast('Voice dictation stopped.');
    } else {
      try {
        baseTextRef.current = userAnswer || '';
        recognition.start();
        setIsRecording(true);
        showToast('Listening... Speak your answer clearly.', 'info');
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleSubmitAnswer = async (e) => {
    if (e) e.preventDefault();
    if (!userAnswer.trim()) {
      showToast('Please enter or dictate an answer before submitting.', 'warning');
      return;
    }

    if (isRecording && recognition) {
      recognition.stop();
      setIsRecording(false);
      baseTextRef.current = '';
    }

    const currentAnswerText = userAnswer;
    const submissionAttemptId = `attempt_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    activeAttemptIdRef.current = submissionAttemptId;

    // Reset previous evaluation state immediately so stale evaluation is never shown
    setEvaluation(null);
    setEvaluating(true);
    showToast('Evaluating answer across technical criteria...', 'info');

    try {
      const res = await interviewApi.evaluateAnswer({
        session_id: currentSessionId || 'default',
        question_id: currentQuestion?.id || `q-${currentIndex}`,
        question_attempt_id: submissionAttemptId,
        question_text: currentQuestion?.question || 'Technical question',
        based_on: currentQuestion?.based_on || 'Resume Context',
        skill: currentQuestion?.skill || 'Technical',
        difficulty: currentQuestion?.difficulty || selectedDifficulty,
        user_answer: currentAnswerText,
        expected_points: currentQuestion?.expected_answer_points || [],
        sample_answer: currentQuestion?.sample_answer || '',
        resume_data: resumeData,
        jd_data: jdData,
        question_intent: currentQuestion?.question_intent || null,
      });

      // Race condition check: ensure only latest active attempt response is processed
      if (activeAttemptIdRef.current !== submissionAttemptId) {
        return;
      }

      const evalData = res.data;
      setEvaluation(evalData);

      const targetKey = getQuestionKey(currentQuestion, currentIndex);
      const updatedMap = {
        ...answeredMap,
        [targetKey]: {
          evaluation: evalData,
          userAnswer: currentAnswerText,
          attemptId: submissionAttemptId,
          questionId: currentQuestion?.id,
          questionText: currentQuestion?.question,
          timestamp: Date.now(),
        },
      };
      setAnsweredMap(updatedMap);

      const newAnsweredCount = Object.keys(updatedMap).length;
      if (newAnsweredCount >= totalQuestions && totalQuestions > 0) {
        showToast(`All ${totalQuestions} questions completed! Final evaluation is ready.`, 'success');
      } else {
        showToast(`Answer scored: ${evalData.overall_score}/100.`);
      }
    } catch (err) {
      if (activeAttemptIdRef.current === submissionAttemptId) {
        console.error(err);
        const msg = err.response?.data?.detail || err.message || 'Failed to evaluate answer.';
        showToast(msg, 'error');
      }
    } finally {
      if (activeAttemptIdRef.current === submissionAttemptId) {
        setEvaluating(false);
      }
    }
  };

  const handleGoToNextQuestion = () => {
    if (currentIndex < (questions?.length || 0) - 1) {
      handleSelectQuestion(currentIndex + 1);
    } else if (isAllAnswered) {
      handleFetchFinalEvaluation();
    } else if (isAdaptiveMode && evaluation?.next_recommended_difficulty) {
      setSelectedDifficulty(evaluation.next_recommended_difficulty);
      ensureQuestions(evaluation.next_recommended_difficulty);
    } else {
      showToast('You have reached the end of the question set.', 'info');
    }
  };

  const handlePracticeFollowUp = () => {
    if (!evaluation?.follow_up_question) return;
    const followUpQ = {
      id: `followup-${Date.now()}`,
      instance_id: `followup_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      question: evaluation.follow_up_question,
      question_type: 'Technical Follow-Up',
      skill: currentQuestion?.skill || 'Technical Depth',
      difficulty: isAdaptiveMode ? (evaluation.next_recommended_difficulty || 'Hard') : selectedDifficulty,
      based_on: `Follow-up to: ${currentQuestion?.question?.slice(0, 40)}...`,
      why_this_question: 'Tests real-time problem solving under follow-up conditions.',
      expected_answer_points: evaluation.concepts_missed || ['Key solution', 'Trade-offs']
    };

    setQuestions([...questions, followUpQ]);
    setCurrentIndex(questions.length);
    setUserAnswer('');
    setEvaluation(null);
    showToast('Loaded follow-up question.');
  };

  const handleFetchFinalEvaluation = async () => {
    try {
      setLoadingFinalEval(true);
      showToast('Compiling comprehensive final interview evaluation...', 'info');

      const evaluationsList = Object.values(answeredMap).map((item) => item.evaluation).filter(Boolean);

      const res = await interviewApi.getFinalEvaluation({
        session_id: currentSessionId || 'default',
        questions: questions || [],
        evaluations: evaluationsList,
        resume_data: resumeData,
        jd_data: jdData,
      });

      setFinalEvaluation(res.data);
      setViewMode('final_evaluation');
      showToast('Final interview evaluation report generated!', 'success');
    } catch (err) {
      console.error('Failed to generate final evaluation:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to generate final evaluation.';
      showToast(msg, 'error');
    } finally {
      setLoadingFinalEval(false);
    }
  };

  const handleExportPdfReport = async () => {
    try {
      setExportingPdf(true);
      showToast('Generating official PDF interview report...', 'info');
      const evaluationsList = Object.values(answeredMap).map((item) => item.evaluation).filter(Boolean);

      const res = await reportApi.exportPdf(currentSessionId || 'default', {
        resume: resumeData,
        jd: jdData,
        evaluations: evaluationsList,
        final_evaluation: finalEvaluation,
      });

      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Interview_Evaluation_Report_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast('PDF report downloaded successfully.', 'success');
    } catch (err) {
      console.error('PDF export failed:', err);
      showToast('Failed to export PDF report.', 'error');
    } finally {
      setExportingPdf(false);
    }
  };

  const handleRetryWeakQuestions = () => {
    const weakQuestions = questions.filter((q, idx) => {
      const k = getQuestionKey(q, idx);
      const ans = answeredMap[k];
      return ans && ans.evaluation && ans.evaluation.overall_score < 70;
    });

    if (weakQuestions.length === 0) {
      showToast('Great job! You scored 70+ on all questions. Loading harder questions...', 'info');
      setSelectedDifficulty('Hard');
      ensureQuestions('Hard');
      return;
    }

    const refreshedWeakQuestions = weakQuestions.map((q, i) => ({
      ...q,
      instance_id: `reattempt_${Date.now()}_${i}_${Math.random().toString(36).substring(2, 7)}`,
    }));

    setQuestions(refreshedWeakQuestions);
    setAnsweredMap({});
    setCurrentIndex(0);
    setUserAnswer('');
    setEvaluation(null);
    setViewMode('interview');
    showToast(`Loaded ${refreshedWeakQuestions.length} questions for targeted practice.`, 'info');
  };

  const copyEvaluationSummaryText = () => {
    if (!finalEvaluation) return;
    const summaryText = `--- MOCK INTERVIEW FINAL EVALUATION ---
Overall Score: ${finalEvaluation.overall_score}/100
Hiring Verdict: ${finalEvaluation.hiring_verdict}
Total Questions Evaluated: ${finalEvaluation.total_questions}

Executive Summary:
${finalEvaluation.executive_summary}

Competencies:
${Object.entries(finalEvaluation.competency_scores || {}).map(([k, v]) => `- ${k}: ${v}/100`).join('\n')}

Key Strengths:
${(finalEvaluation.key_strengths || []).map((s) => `+ ${s}`).join('\n')}

Areas for Growth:
${(finalEvaluation.critical_weaknesses || []).map((w) => `- ${w}`).join('\n')}

Actionable Next Steps:
${(finalEvaluation.actionable_recommendations || []).map((r, i) => `${i + 1}. ${r}`).join('\n')}
`;
    navigator.clipboard.writeText(summaryText);
    setCopiedSummary(true);
    setTimeout(() => setCopiedSummary(false), 2000);
    showToast('Evaluation summary copied to clipboard.');
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Title Header & Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            {viewMode === 'final_evaluation' ? 'Mock Interview Final Evaluation' : 'Mock Interview Practice'}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {viewMode === 'final_evaluation'
              ? 'Comprehensive performance synthesis, 6-axis competencies, and actionable hiring feedback.'
              : 'Answer questions in text or speech and receive real-time criteria feedback and model answers.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {viewMode === 'final_evaluation' ? (
            <button
              onClick={() => setViewMode('interview')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Questions</span>
            </button>
          ) : (
            <>
              <span className="text-xs text-slate-700 bg-white border border-slate-200 px-2.5 py-1 rounded-md font-semibold">
                Question {totalQuestions > 0 ? currentIndex + 1 : 0} of {totalQuestions}
              </span>
              <span className={`text-xs px-2.5 py-1 rounded-md font-semibold border ${
                isAllAnswered
                  ? 'bg-emerald-100/70 text-emerald-800 border-emerald-300'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200/60'
              }`}>
                Answered: {answeredCount}/{totalQuestions} {isAllAnswered && '✓'}
              </span>
              {isAllAnswered && (
                <button
                  onClick={handleFetchFinalEvaluation}
                  disabled={loadingFinalEval}
                  className="inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-md text-xs font-bold shadow-sm transition-all animate-pulse"
                >
                  <Trophy className="w-3.5 h-3.5" />
                  <span>{loadingFinalEval ? 'Evaluating...' : 'View Final Evaluation'}</span>
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Active Resume Source Indicator */}
      {resumeData && (
        <div className="p-3 bg-white border border-slate-200 rounded-xl flex flex-wrap items-center justify-between gap-3 text-xs shadow-2xs">
          <div className="flex items-center gap-2 flex-wrap">
            <FileText className="w-4 h-4 text-blue-600" />
            <span className="font-bold text-slate-900">{resumeData.filename || resumeData.name + '_Resume.pdf'}</span>
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded text-[11px] font-semibold">
              ✓ Verified Resume ({Math.round((resumeData.resume_confidence || 0.95) * 100)}% Confidence)
            </span>
          </div>
          <div className="text-slate-500 font-mono text-[11px]">
            Target Resume ID: {resumeData.id ? `${resumeData.id.slice(0, 13)}...` : 'active'}
          </div>
        </div>
      )}

      {/* Completion Banner (when in interview mode and all answered) */}
      {viewMode === 'interview' && isAllAnswered && (
        <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-emerald-50 border border-blue-200/80 rounded-xl p-4 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold shadow-sm flex-shrink-0">
              <Trophy className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900">All {totalQuestions} Questions Completed!</h4>
              <p className="text-xs text-slate-600 mt-0.5">
                You have submitted answers for the full question queue. View your final hiring evaluation, 6-axis score matrix, and actionable feedback.
              </p>
            </div>
          </div>
          <button
            onClick={handleFetchFinalEvaluation}
            disabled={loadingFinalEval}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm transition-all whitespace-nowrap"
          >
            <Sparkles className="w-4 h-4" />
            <span>{loadingFinalEval ? 'Compiling Final Report...' : '✨ Generate Final Evaluation Report'}</span>
          </button>
        </div>
      )}

      {/* View Mode: FINAL EVALUATION REPORT */}
      {viewMode === 'final_evaluation' && finalEvaluation ? (
        <div className="space-y-6">
          {/* Executive Overview Hero Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-5">
            <div className="flex flex-col lg:flex-row items-center justify-between gap-6 pb-5 border-b border-slate-100">
              {/* Score & Verdict */}
              <div className="flex flex-col sm:flex-row items-center gap-5 text-center sm:text-left">
                <ScoreRing
                  score={finalEvaluation.overall_score}
                  size={104}
                  strokeWidth={8}
                  label="Final Score"
                />
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Hiring Decision:</span>
                    <Badge variant={finalEvaluation.verdict_badge || 'primary'} size="sm">
                      {finalEvaluation.hiring_verdict}
                    </Badge>
                  </div>
                  <h2 className="text-lg font-bold text-slate-900">
                    {finalEvaluation.overall_score >= 85
                      ? 'Exceptional Interview Performance'
                      : finalEvaluation.overall_score >= 70
                      ? 'Solid Technical & Problem-Solving Competence'
                      : finalEvaluation.overall_score >= 50
                      ? 'Developing Candidate with Growth Areas'
                      : 'Significant Preparation Needed'}
                  </h2>
                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 text-xs text-slate-500">
                    <span className="inline-flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                      <Target className="w-3 h-3 text-blue-600" />
                      <span>{finalEvaluation.total_questions} Questions Evaluated</span>
                    </span>
                    <span className="inline-flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                      <Flame className="w-3 h-3 text-amber-500" />
                      <span>Technical Level: {selectedDifficulty}</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons Toolbar */}
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={copyEvaluationSummaryText}
                  className="flex items-center gap-1.5 px-3 py-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors shadow-2xs"
                >
                  {copiedSummary ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedSummary ? 'Copied' : 'Copy Summary'}</span>
                </button>

                <button
                  onClick={handleExportPdfReport}
                  disabled={exportingPdf}
                  className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>{exportingPdf ? 'Exporting PDF...' : 'Download PDF Report'}</span>
                </button>
              </div>
            </div>

            {/* Executive Synthesis Narrative */}
            <div className="bg-slate-50/70 rounded-xl p-4 border border-slate-200/80 space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wide">
                <FileText className="w-3.5 h-3.5 text-blue-600" />
                <span>Interviewer Executive Synthesis:</span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-normal">
                {finalEvaluation.executive_summary}
              </p>
            </div>
          </div>

          {/* 6-Axis Competency Grid */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">6-Axis Competency Breakdown</h3>
              </div>
              <span className="text-[11px] text-slate-500">Benchmark: 70+ Recommended for Hire</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {Object.entries(finalEvaluation.competency_scores || {}).map(([compName, score], idx) => {
                const isHigh = score >= 75;
                const isMid = score >= 50 && score < 75;
                return (
                  <div key={idx} className="p-3.5 bg-slate-50/70 rounded-xl border border-slate-200/80 space-y-2 text-center">
                    <span className="text-[11px] font-semibold text-slate-600 block truncate" title={compName}>
                      {compName}
                    </span>
                    <div className="text-lg font-bold text-slate-900">
                      {score}<span className="text-xs font-normal text-slate-400">/100</span>
                    </div>
                    <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          isHigh ? 'bg-emerald-500' : isMid ? 'bg-amber-500' : 'bg-rose-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Strengths & Critical Areas for Growth */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Key Strengths */}
            <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm pb-2 border-b border-slate-100">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Demonstrated Technical Strengths</span>
              </div>
              <ul className="space-y-2.5">
                {finalEvaluation.key_strengths?.map((str, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 flex-shrink-0" />
                    <span className="leading-relaxed">{str}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Critical Weaknesses / Missed Concepts */}
            <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-amber-800 font-bold text-sm pb-2 border-b border-slate-100">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                <span>Areas for Technical Deepening</span>
              </div>
              <ul className="space-y-2.5">
                {finalEvaluation.critical_weaknesses?.map((weak, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 flex-shrink-0" />
                    <span className="leading-relaxed">{weak}</span>
                  </li>
                ))}
                {finalEvaluation.missed_concepts && finalEvaluation.missed_concepts.length > 0 && (
                  <li className="pt-2 border-t border-slate-100">
                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wide block mb-1">
                      Key Concepts Missed in Answers:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {finalEvaluation.missed_concepts.map((concept, cIdx) => (
                        <span key={cIdx} className="text-[11px] bg-amber-50 text-amber-900 border border-amber-200/80 px-2 py-0.5 rounded-md">
                          {concept}
                        </span>
                      ))}
                    </div>
                  </li>
                )}
              </ul>
            </div>
          </div>

          {/* Actionable Study Roadmap */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 font-bold text-sm text-blue-200 pb-2 border-b border-slate-700/80">
              <BookOpen className="w-4 h-4 text-blue-400" />
              <span>Targeted Preparation Roadmap (Before Real Interviews)</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
              {finalEvaluation.actionable_recommendations?.map((rec, idx) => (
                <div key={idx} className="p-3 bg-slate-800/80 rounded-lg border border-slate-700/60 space-y-1">
                  <div className="text-[11px] font-bold text-blue-400 uppercase tracking-wider">Priority #{idx + 1}</div>
                  <p className="text-xs text-slate-200 leading-relaxed font-light">{rec}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Question-by-Question Review Breakdown */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Per-Question Evaluation Breakdown</h3>
              </div>
              <span className="text-xs text-slate-500">{finalEvaluation.per_question_breakdown?.length || 0} Questions</span>
            </div>

            <div className="space-y-3">
              {finalEvaluation.per_question_breakdown?.map((item, idx) => {
                const isExpanded = expandedQuestionIdx === idx;
                return (
                  <div key={item.question_id || idx} className="border border-slate-200 rounded-lg overflow-hidden transition-all">
                    <button
                      type="button"
                      onClick={() => setExpandedQuestionIdx(isExpanded ? null : idx)}
                      className="w-full p-3.5 bg-slate-50/50 hover:bg-slate-50 flex items-center justify-between gap-3 text-left transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <span className="w-6 h-6 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
                          #{idx + 1}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-bold text-slate-900 truncate">
                            {item.question_text}
                          </p>
                          <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                            <span>Topic: <span className="font-semibold text-slate-700">{item.skill}</span></span>
                            <span>•</span>
                            <span>Diff: <span className="font-semibold text-slate-700">{item.difficulty}</span></span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 flex-shrink-0">
                        <Badge variant={item.score >= 70 ? 'success' : item.score >= 50 ? 'warning' : 'danger'}>
                          {item.score}/100 • {item.verdict}
                        </Badge>
                        {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="p-4 bg-white border-t border-slate-100 space-y-3">
                        <div className="space-y-1">
                          <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">Key Feedback Summary:</span>
                          <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-2.5 rounded-md border border-slate-100">
                            {item.key_feedback}
                          </p>
                        </div>

                        {item.user_answer_snippet && (
                          <div className="space-y-1">
                            <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">Suggested Benchmark Response:</span>
                            <p className="text-xs text-slate-600 italic leading-relaxed bg-blue-50/40 p-2.5 rounded-md border border-blue-100">
                              {item.user_answer_snippet}
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Bottom Actions Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <button
              onClick={() => setViewMode('interview')}
              className="flex items-center gap-1.5 px-4 py-2 border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-xs font-semibold rounded-lg transition-colors shadow-2xs"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Review Interview Questions</span>
            </button>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleRetryWeakQuestions}
                className="flex items-center gap-1.5 px-4 py-2 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200/80 text-xs font-semibold rounded-lg transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5 text-amber-700" />
                <span>Re-attempt Weak Questions (&lt;70)</span>
              </button>

              <button
                onClick={() => ensureQuestions(selectedDifficulty)}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-all"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Start New Mock Round</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* View Mode: INTERVIEW PRACTICE QUEUE */
        <>
          {/* Question Selector Bar */}
          <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-sm flex flex-col md:flex-row items-center justify-between gap-3">
            {/* Question Numbers */}
            <div className="flex items-center gap-1 flex-wrap">
              <span className="text-[11px] font-bold text-slate-500 mr-2 uppercase tracking-wide">Queue:</span>
              {questions && questions.map((q, idx) => {
                const qKey = getQuestionKey(q, idx);
                const isAnswered = Boolean(answeredMap[qKey]);
                const isCurrent = idx === currentIndex;
                return (
                  <button
                    key={q.instance_id || q.id || idx}
                    onClick={() => handleSelectQuestion(idx)}
                    className={`relative px-2.5 py-1 rounded-md text-xs font-semibold transition-colors ${
                      isCurrent
                        ? 'bg-blue-600 text-white'
                        : isAnswered
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200/70 hover:bg-emerald-100'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    <span>#{idx + 1}</span>
                    {isAnswered && (
                      <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    )}
                  </button>
                );
              })}

              <button
                onClick={() => ensureQuestions(selectedDifficulty)}
                disabled={loadingQuestions}
                className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 px-2 py-1 rounded-md border border-blue-200/60 transition-colors ml-1"
              >
                <PlusCircle className="w-3 h-3" />
                <span>Generate More</span>
              </button>
            </div>

            {/* Difficulty Selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-600 font-medium">Difficulty:</span>
              <select
                value={selectedDifficulty}
                onChange={(e) => {
                  setSelectedDifficulty(e.target.value);
                  ensureQuestions(e.target.value);
                }}
                className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-md px-2 py-1 text-slate-800 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              >
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
                <option value="Expert">Expert</option>
              </select>
            </div>
          </div>

          {currentQuestion ? (
            <div className="space-y-4">
              {/* Current Question Card */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <Badge variant={currentQuestion.difficulty?.toLowerCase()} size="xs">
                      {currentQuestion.difficulty}
                    </Badge>
                    <Badge variant="primary" size="xs">
                      {currentQuestion.skill}
                    </Badge>
                    <Badge variant="default" size="xs">
                      {currentQuestion.question_type}
                    </Badge>
                    {currentQuestion.question_intent && (
                      <span className="text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/80 px-2 py-0.5 rounded-md">
                        Intent: {currentQuestion.question_intent.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>

                  {currentQuestion.based_on && (
                    <span className="text-[11px] text-slate-500">
                      Based on: <span className="text-slate-700 font-medium">{currentQuestion.based_on}</span>
                    </span>
                  )}
                </div>

                <h3 className="text-base font-bold text-slate-900 leading-snug">
                  {currentQuestion.question}
                </h3>

                {currentQuestion.why_this_question && (
                  <p className="text-xs text-slate-500 pt-1 border-t border-slate-100">
                    <span className="font-semibold text-slate-700">Evaluation Goal:</span> {currentQuestion.why_this_question}
                  </p>
                )}
              </div>

              {/* Answer Input Card */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                    Your Answer
                  </label>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span>{wordCount} words</span>
                    <button
                      type="button"
                      onClick={toggleRecording}
                      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border transition-colors ${
                        isRecording
                          ? 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {isRecording ? <MicOff className="w-3.5 h-3.5 text-rose-600" /> : <Mic className="w-3.5 h-3.5 text-slate-600" />}
                      <span>{isRecording ? 'Listening...' : 'Voice Dictate'}</span>
                    </button>
                  </div>
                </div>

                <textarea
                  rows={6}
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  placeholder="Type your response here or click 'Voice Dictate' to speak. Structure your answer using real technical experiences, trade-offs, and metrics..."
                  className="w-full text-xs font-sans p-3.5 border border-slate-200 rounded-lg focus:ring-1 focus:ring-blue-500 focus:outline-none bg-slate-50/40 text-slate-900 leading-relaxed"
                />

                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setUserAnswer('');
                        baseTextRef.current = '';
                      }}
                      className="text-xs text-slate-400 hover:text-slate-600"
                    >
                      Clear text
                    </button>
                  </div>

                  <button
                    onClick={handleSubmitAnswer}
                    disabled={evaluating || !userAnswer.trim()}
                    className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{evaluating ? 'Evaluating Answer...' : 'Submit Answer for Feedback'}</span>
                  </button>
                </div>
              </div>

              {/* Evaluating In-Progress Banner */}
              {evaluating && (
                <div className="bg-white border border-blue-200/90 rounded-xl p-6 shadow-sm flex flex-col items-center justify-center text-center space-y-3">
                  <div className="w-10 h-10 rounded-full border-3 border-blue-600 border-t-transparent animate-spin flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">Evaluating Answer in Real Time...</h4>
                    <p className="text-xs text-slate-500 mt-1 max-w-md">
                      Analyzing technical accuracy, relevance, completeness, and clarity against expected benchmark criteria.
                    </p>
                  </div>
                </div>
              )}

              {/* 6-Axis Evaluation Results */}
              {!evaluating && evaluation && (
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                  {/* Header Score & Verdict */}
                  <div className="flex flex-col sm:flex-row items-center gap-6 pb-4 border-b border-slate-100">
                    <ScoreRing score={evaluation.overall_score ?? 0} size={88} strokeWidth={7} label="Answer Score" />
                    <div className="space-y-1.5 flex-1 text-center sm:text-left">
                      <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                        <h3 className="text-base font-bold text-slate-900">Answer Evaluation</h3>
                        <Badge variant={evaluation.overall_score >= 75 ? 'success' : evaluation.overall_score >= 50 ? 'warning' : 'danger'}>
                          {evaluation.verdict_rating || evaluation.verdict || (
                            evaluation.overall_score >= 85 ? 'Exceptional' :
                            evaluation.overall_score >= 70 ? 'Strong Answer' :
                            evaluation.overall_score >= 50 ? 'Adequate Answer' :
                            evaluation.overall_score > 0 ? 'Needs Technical Depth' : 'No Answer Provided'
                          )}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {evaluation.feedback_summary || evaluation.rationale}
                      </p>
                    </div>
                  </div>

                  {/* 6-Axis Sub-Scores */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                    {[
                      { label: "Relevance", val: evaluation.relevance_score ?? evaluation.axis_scores?.relevance ?? 0 },
                      { label: "Technical Depth", val: evaluation.technical_accuracy_score ?? evaluation.axis_scores?.technical ?? 0 },
                      { label: "Completeness", val: evaluation.completeness_score ?? evaluation.axis_scores?.completeness ?? 0 },
                      { label: "Clarity", val: evaluation.clarity_score ?? evaluation.axis_scores?.clarity ?? 0 },
                      { label: "Confidence", val: evaluation.confidence_score ?? evaluation.axis_scores?.confidence ?? 0 },
                      { label: "Communication", val: evaluation.communication_score ?? evaluation.axis_scores?.communication ?? 0 },
                    ].map((axis, idx) => (
                      <div key={idx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-center">
                        <div className="text-[11px] text-slate-500">{axis.label}</div>
                        <div className="text-sm font-bold text-slate-800 mt-0.5">{axis.val}/100</div>
                      </div>
                    ))}
                  </div>

                  {/* Strengths & Missed Concepts */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                    {/* Strengths */}
                    <div className="p-3.5 bg-emerald-50/40 rounded-lg border border-emerald-100 space-y-2">
                      <div className="flex items-center gap-1.5 text-emerald-800 font-bold text-xs">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Answer Strengths</span>
                      </div>
                      <ul className="space-y-1.5">
                        {evaluation.strengths?.map((s, idx) => (
                          <li key={idx} className="flex items-start gap-1.5 text-xs text-slate-700">
                            <span className="text-emerald-500 font-bold">•</span>
                            <span>{s}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Missed Concepts */}
                    <div className="p-3.5 bg-amber-50/40 rounded-lg border border-amber-100 space-y-2">
                      <div className="flex items-center gap-1.5 text-amber-800 font-bold text-xs">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                        <span>Missed Concepts / Growth</span>
                      </div>
                      <ul className="space-y-1.5">
                        {(evaluation.concepts_missed || evaluation.weaknesses)?.map((w, idx) => (
                          <li key={idx} className="flex items-start gap-1.5 text-xs text-slate-700">
                            <span className="text-amber-500 font-bold">•</span>
                            <span>{w}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Model Answer */}
                  {(() => {
                    let rawAns = evaluation.improved_answer || currentQuestion.sample_answer;
                    if (!rawAns) {
                      rawAns = `When working with ${currentQuestion.skill || 'this technology'}, my approach focuses on understanding core mechanisms, establishing clean validation boundaries, and managing performance trade-offs based on application requirements.`;
                    }
                    const isHighScorer = (evaluation.overall_score || 0) >= 75;
                    return (
                      <div className="p-4 bg-slate-50/80 rounded-xl border border-slate-200 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-900 uppercase tracking-wide flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            {isHighScorer ? 'Staff-Level Architectural Enhancement:' : 'Suggested Model Answer (Ideal Interview Response):'}
                          </span>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(rawAns);
                              setCopiedModel(true);
                              setTimeout(() => setCopiedModel(false), 2000);
                              showToast('Suggested model answer copied.');
                            }}
                            className="flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 bg-white px-2.5 py-1 rounded-md border border-slate-200 transition-colors shadow-2xs"
                          >
                            {copiedModel ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                            <span>{copiedModel ? 'Copied' : 'Copy Answer'}</span>
                          </button>
                        </div>
                        <div className="text-xs text-slate-800 leading-relaxed bg-white p-3.5 rounded-lg border border-slate-200/80 shadow-2xs font-normal">
                          {rawAns}
                        </div>

                        {/* Grounding & Intent Badges */}
                        {(evaluation.question_intent || evaluation.answer_structure || evaluation.answer_grounding) && (
                          <div className="flex flex-wrap items-center gap-1.5 text-[10px] pt-0.5">
                            {evaluation.question_intent && (
                              <span className="bg-white text-slate-700 font-medium px-2 py-0.5 rounded border border-slate-200 shadow-2xs">
                                Intent: <span className="font-semibold text-slate-900">{evaluation.question_intent.replace(/_/g, ' ')}</span>
                              </span>
                            )}
                            {evaluation.answer_structure && (
                              <span className="bg-white text-slate-700 font-medium px-2 py-0.5 rounded border border-slate-200 shadow-2xs">
                                Structure: <span className="font-semibold text-slate-900">{evaluation.answer_structure}</span>
                              </span>
                            )}
                            {evaluation.answer_grounding && (
                              <span className={`px-2 py-0.5 rounded font-semibold border ${
                                evaluation.answer_grounding.badge_variant === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' :
                                evaluation.answer_grounding.badge_variant === 'warning' ? 'bg-amber-50 text-amber-800 border-amber-200' :
                                'bg-blue-50 text-blue-800 border-blue-200'
                              }`}>
                                ✓ {evaluation.answer_grounding.status}
                              </span>
                            )}
                          </div>
                        )}
                        {currentQuestion.expected_answer_points && currentQuestion.expected_answer_points.length > 0 && (
                          <div className="text-[11px] text-slate-600 bg-slate-100/70 p-2.5 rounded-md border border-slate-200/60 flex flex-wrap items-center gap-1.5">
                            <span className="font-semibold text-slate-800 mr-1">Interviewer Checkpoints:</span>
                            {currentQuestion.expected_answer_points.map((pt, idx) => (
                              <span key={idx} className="inline-flex items-center bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-700">
                                {pt}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })()}

                  {/* Action Buttons */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                    {evaluation.follow_up_question ? (
                      <button
                        onClick={handlePracticeFollowUp}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-lg transition-colors"
                      >
                        <span>Practice Follow-Up Question</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    ) : <div />}

                    <div className="flex items-center gap-2 ml-auto">
                      {isAllAnswered ? (
                        <button
                          onClick={handleFetchFinalEvaluation}
                          disabled={loadingFinalEval}
                          className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold rounded-lg shadow-sm transition-all"
                        >
                          <Trophy className="w-3.5 h-3.5" />
                          <span>{loadingFinalEval ? 'Evaluating...' : 'View Final Interview Evaluation'}</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      ) : (
                        <button
                          onClick={handleGoToNextQuestion}
                          className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                        >
                          <span>Next Question</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : !resumeData ? (
            <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
              <FileText className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-sm font-bold text-slate-700">No active resume uploaded</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Upload your resume to generate grounded interview questions and start your mock interview.
              </p>
              <button
                onClick={() => navigate('/resume')}
                className="mt-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
              >
                <span>Upload Resume to Begin</span>
              </button>
            </div>
          ) : (
            <div className="p-8 bg-white rounded-xl border border-slate-200 text-center space-y-2">
              <HelpCircle className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-sm font-bold text-slate-700">No questions loaded for practice</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Generate interview questions from your resume to begin a mock interview.
              </p>
              <button
                onClick={() => ensureQuestions(selectedDifficulty)}
                className="mt-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
              >
                <span>Load 5 Questions</span>
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Voice Dictation Live Pulse - Chapala Keerthana
