import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { questionsApi, interviewApi } from '../services/api';
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
  ChevronUp
} from 'lucide-react';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';

export const MockInterview = () => {
  const location = useLocation();
  const { resumeData, jdData, currentSessionId, questions, setQuestions, showToast } = useSession();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [evaluating, setEvaluating] = useState(false);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [answeredMap, setAnsweredMap] = useState({});
  const [selectedDifficulty, setSelectedDifficulty] = useState('Medium');
  const [isAdaptiveMode, setIsAdaptiveMode] = useState(false);
  const [copiedModel, setCopiedModel] = useState(false);

  // Speech Recognition instance
  const [recognition, setRecognition] = useState(null);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognizer = new SpeechRecognition();
      recognizer.continuous = true;
      recognizer.interimResults = true;
      recognizer.lang = 'en-US';

      recognizer.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setUserAnswer((prev) => (prev ? `${prev} ${transcript}` : transcript));
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
        setQuestions(res.data);
        setCurrentIndex(0);
        setUserAnswer('');
        setEvaluation(null);
        showToast(`Loaded ${res.data.length} interview questions.`);
      }
    } catch (err) {
      console.error('Failed to generate questions:', err);
    } finally {
      setLoadingQuestions(false);
    }
  };

  useEffect(() => {
    if (location.state?.selectedQuestion) {
      const q = location.state.selectedQuestion;
      if (questions && questions.length > 0) {
        const foundIdx = questions.findIndex((item) => item.id === q.id);
        if (foundIdx !== -1) {
          setCurrentIndex(foundIdx);
        } else {
          setQuestions([q, ...questions]);
          setCurrentIndex(0);
        }
      } else {
        setQuestions([q]);
        setCurrentIndex(0);
      }
    } else if (resumeData && (!questions || questions.length === 0)) {
      ensureQuestions('Medium');
    }
  }, [resumeData, location.state]);

  const currentQuestion = questions && questions.length > 0 ? questions[currentIndex] : null;

  const handleSelectQuestion = (index) => {
    if (index < 0 || index >= (questions?.length || 0)) return;
    if (isRecording && recognition) {
      recognition.stop();
      setIsRecording(false);
    }
    setCurrentIndex(index);
    const targetQ = questions[index];
    if (targetQ && answeredMap[targetQ.id]) {
      setEvaluation(answeredMap[targetQ.id].evaluation);
      setUserAnswer(answeredMap[targetQ.id].userAnswer || '');
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
      showToast('Voice dictation stopped.');
    } else {
      try {
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
    }

    try {
      setEvaluating(true);
      showToast('Evaluating answer across technical criteria...', 'info');

      const res = await interviewApi.evaluateAnswer({
        session_id: currentSessionId || 'default',
        question_id: currentQuestion?.id || `q-${currentIndex}`,
        question_text: currentQuestion?.question || 'Technical question',
        based_on: currentQuestion?.based_on || 'Resume Context',
        skill: currentQuestion?.skill || 'Technical',
        difficulty: currentQuestion?.difficulty || selectedDifficulty,
        user_answer: userAnswer,
        expected_points: currentQuestion?.expected_answer_points || [],
      });

      let evalData = res.data;

      // Strict Zero-Score Enforcement for Random / Gibberish / Off-Topic / Short answers
      const cleaned = userAnswer.trim().toLowerCase();
      const words = cleaned.split(/\s+/).filter((w) => w.length > 0);
      const isRandomOrGibberish =
        words.length < 4 ||
        (evalData.overall_score != null && evalData.overall_score <= 25) ||
        /^[bcdfghjklmnpqrstvwxyz\W_]+$/i.test(cleaned) ||
        cleaned.includes(';') ||
        /(.)\1{4,}/.test(cleaned) ||
        (evalData.verdict_rating && (
          evalData.verdict_rating.toLowerCase().includes('incomplete') ||
          evalData.verdict_rating.toLowerCase().includes('insufficient') ||
          evalData.verdict_rating.toLowerCase().includes('random') ||
          evalData.verdict_rating.toLowerCase().includes('irrelevant') ||
          evalData.verdict_rating.toLowerCase().includes('no answer')
        ));

      if (isRandomOrGibberish) {
        evalData = {
          ...evalData,
          overall_score: 0,
          relevance_score: 0,
          technical_accuracy_score: 0,
          completeness_score: 0,
          clarity_score: 0,
          confidence_score: 0,
          communication_score: 0,
          verdict_rating: words.length < 4 ? 'No Answer Provided' : 'Irrelevant / Random Input',
          feedback_summary: 'Random, off-topic, or insufficient input detected (0/100). Review the suggested model answer below.',
          strengths: ['No relevant technical substance identified.'],
          weaknesses: [
            `The answer entered did not provide a valid technical explanation for ${currentQuestion?.skill || 'this question'}.`,
            'Explain concrete system mechanisms, implementation choices, and practical trade-offs.'
          ]
        };
      }

      setEvaluation(evalData);
      if (currentQuestion?.id) {
        setAnsweredMap((prev) => ({
          ...prev,
          [currentQuestion.id]: {
            evaluation: evalData,
            userAnswer: userAnswer,
          },
        }));
      }

      showToast(`Answer scored: ${evalData.overall_score}/100.`);
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || err.message || 'Failed to evaluate answer.';
      showToast(msg, 'error');
    } finally {
      setEvaluating(false);
    }
  };

  const handleGoToNextQuestion = () => {
    if (currentIndex < (questions?.length || 0) - 1) {
      handleSelectQuestion(currentIndex + 1);
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

  const copyModelAnswer = () => {
    const textToCopy = evaluation?.improved_answer || currentQuestion?.sample_answer;
    if (!textToCopy) return;
    navigator.clipboard.writeText(textToCopy);
    setCopiedModel(true);
    setTimeout(() => setCopiedModel(false), 2000);
    showToast('Suggested model answer copied.');
  };

  const totalQuestions = questions?.length || 0;
  const answeredCount = Object.keys(answeredMap).length;
  const wordCount = userAnswer.trim() ? userAnswer.trim().split(/\s+/).length : 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Mock Interview Practice</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Answer questions in text or speech and receive criteria feedback and model answers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-700 bg-white border border-slate-200 px-2.5 py-1 rounded-md font-semibold">
            Question {totalQuestions > 0 ? currentIndex + 1 : 0} of {totalQuestions}
          </span>
          <span className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-2.5 py-1 rounded-md font-medium">
            Answered: {answeredCount}/{totalQuestions}
          </span>
        </div>
      </div>

      {/* Question Selector Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-sm flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Question Numbers */}
        <div className="flex items-center gap-1 flex-wrap">
          <span className="text-[11px] font-bold text-slate-500 mr-2 uppercase tracking-wide">Queue:</span>
          {questions && questions.map((q, idx) => {
            const isAnswered = Boolean(answeredMap[q.id]);
            const isCurrent = idx === currentIndex;
            return (
              <button
                key={q.id || idx}
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
              <div className="flex items-center gap-1.5">
                <Badge variant={currentQuestion.difficulty?.toLowerCase()} size="xs">
                  {currentQuestion.difficulty}
                </Badge>
                <Badge variant="primary" size="xs">
                  {currentQuestion.skill}
                </Badge>
                <Badge variant="default" size="xs">
                  {currentQuestion.question_type}
                </Badge>
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
                  onClick={() => setUserAnswer('')}
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

          {/* 6-Axis Evaluation Results */}
          {evaluation && (
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
                if (!rawAns || rawAns.toLowerCase().startsWith("to answer effectively") || rawAns.toLowerCase().startsWith("a strong answer should")) {
                  rawAns = `In our project, we implemented ${currentQuestion.skill || 'this technology'} to handle core processing with high reliability. We established clear architecture boundaries, optimized data validation and query execution, and handled edge cases defensively. This approach provided resilient throughput, minimal processing overhead, and predictable sub-50ms latency in production.`;
                }
                return (
                  <div className="p-4 bg-slate-50/80 rounded-xl border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 uppercase tracking-wide flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        Suggested Model Answer (Ideal Interview Response):
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

                <button
                  onClick={handleGoToNextQuestion}
                  className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors ml-auto"
                >
                  <span>Next Question</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
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
    </div>
  );
};
