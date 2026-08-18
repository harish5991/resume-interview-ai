import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { sessionsApi, resumeApi, jobApi, matchApi, interviewApi } from '../services/api';
import { FALLBACK_RESUMES, FALLBACK_JDS } from '../utils/fallbackData';

const SessionContext = createContext();

const getSessionCache = (sid) => {
  try {
    const raw = sessionStorage.getItem(`interview_session_cache_${sid}`);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
};

const setSessionCache = (sid, data) => {
  try {
    sessionStorage.setItem(`interview_session_cache_${sid}`, JSON.stringify(data));
  } catch (e) {}
};

const getInitialSessionInfo = () => {
  try {
    const isAppActive = sessionStorage.getItem('interview_app_active');
    const sid = sessionStorage.getItem('interview_session_id');
    if (!isAppActive || !sid) {
      return { sid: 'default', cache: null, hasSavedSession: false, isFreshLaunch: true };
    }
    const raw = sessionStorage.getItem(`interview_session_cache_${sid}`);
    const cache = raw ? JSON.parse(raw) : null;
    return { sid, cache, hasSavedSession: Boolean(cache && cache.resume), isFreshLaunch: false };
  } catch (e) {
    return { sid: 'default', cache: null, hasSavedSession: false, isFreshLaunch: true };
  }
};

export const SessionProvider = ({ children }) => {
  const [sessions, setSessions] = useState([{ id: 'default', name: 'Default Interview Prep' }]);
  
  // Ephemeral vs Persistent settings
  const [autoClearOnClose, setAutoClearOnCloseState] = useState(() => {
    const saved = localStorage.getItem('auto_clear_on_close');
    return saved !== null ? saved === 'true' : true;
  });

  const setAutoClearOnClose = (val) => {
    setAutoClearOnCloseState(val);
    localStorage.setItem('auto_clear_on_close', String(val));
    showToast(val ? 'Auto-clear on close enabled.' : 'Persistent history mode enabled.');
  };

  // Synchronously restore state if preserved across browser refresh in sessionStorage
  const initialInfo = getInitialSessionInfo();
  const [currentSessionId, setCurrentSessionIdState] = useState(initialInfo.sid);

  // Active session state: restored on browser refresh, clean on fresh browser open
  const [resumeData, setResumeDataState] = useState(initialInfo.cache?.resume || null);
  const [resumeScore, setResumeScore] = useState(initialInfo.cache?.resume_score || null);
  const [jdData, setJdDataState] = useState(initialInfo.cache?.jd || null);
  const [matchData, setMatchData] = useState(initialInfo.cache?.match || null);
  const [questions, setQuestionsState] = useState(initialInfo.cache?.questions || []);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  // Request counter to prevent async race conditions
  const activeRequestRef = useRef(0);

  const showToast = (message, type = 'success') => {
    setToast({ message, type, id: Date.now() });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  const persistToBackendAndCache = useCallback(async (sid, updates) => {
    // 1. Update session storage cache for current session
    const current = getSessionCache(sid) || {};
    const merged = { ...current, ...updates };
    setSessionCache(sid, merged);

    // 2. Persist to backend database session
    try {
      await sessionsApi.update(sid, updates);
    } catch (e) {
      console.warn('Could not sync session to backend:', e);
    }
  }, []);

  const clearSessionHistory = async () => {
    try {
      await interviewApi.clearHistory(currentSessionId);
      showToast('Question and interview history cleared.');
    } catch (e) {
      console.log('Error clearing history:', e);
    }
  };

  // Explicit session switching (user explicitly chooses a session from dropdown / manager)
  const switchSession = async (newSessionId) => {
    activeRequestRef.current += 1;
    setCurrentSessionIdState(newSessionId);
    sessionStorage.setItem('interview_session_id', newSessionId);

    // Clear active state first
    setResumeDataState(null);
    setResumeScore(null);
    setJdDataState(null);
    setMatchData(null);
    setQuestionsState([]);

    // Hydrate explicitly from backend for this selected session
    try {
      const res = await sessionsApi.get(newSessionId);
      if (res.data) {
        const d = res.data;
        if (d.resume) setResumeDataState(d.resume);
        if (d.resume_score) setResumeScore(d.resume_score);
        if (d.jd) setJdDataState(d.jd);
        if (d.match) setMatchData(d.match);
        if (d.questions) setQuestionsState(d.questions);
        setSessionCache(newSessionId, d);
      }
    } catch (e) {
      console.log('Error loading session from backend:', e);
    }
  };

  // Explicit demo/sample data loader
  const loadSampleData = async () => {
    const reqId = ++activeRequestRef.current;
    try {
      setLoading(true);
      sessionStorage.setItem('interview_app_active', 'true');
      sessionStorage.setItem('interview_session_id', currentSessionId);
      sessionStorage.removeItem(`mock_interview_progress_${currentSessionId}`);

      let defaultResume = FALLBACK_RESUMES[0];
      let defaultJd = FALLBACK_JDS[0];

      try {
        const sampleRes = await resumeApi.getSamples();
        if (sampleRes.data && sampleRes.data.length > 0) {
          defaultResume = sampleRes.data[0];
        }
      } catch (e) {}

      try {
        const sampleJds = await jobApi.getSamples();
        if (sampleJds.data && sampleJds.data.length > 0) {
          defaultJd = sampleJds.data[0];
        }
      } catch (e) {}

      let calculatedScore = null;
      let calculatedMatch = null;

      if (defaultResume) {
        try {
          const scoreRes = await resumeApi.analyze(defaultResume);
          calculatedScore = scoreRes.data.score;
        } catch (e) {}
      }

      if (defaultResume && defaultJd) {
        try {
          const matchRes = await matchApi.match(defaultResume, defaultJd);
          calculatedMatch = matchRes.data;
        } catch (e) {}
      }

      if (reqId !== activeRequestRef.current) return;

      setResumeDataState(defaultResume);
      setResumeScore(calculatedScore);
      setJdDataState(defaultJd);
      setMatchData(calculatedMatch);

      await persistToBackendAndCache(currentSessionId, {
        resume: defaultResume,
        resume_score: calculatedScore,
        jd: defaultJd,
        match: calculatedMatch,
        questions: [],
      });

      showToast('Sample profile (Alex Chen) loaded.');
    } catch (err) {
      console.error('Error loading sample data:', err);
      showToast('Failed to load demo data.', 'error');
    } finally {
      if (reqId === activeRequestRef.current) {
        setLoading(false);
      }
    }
  };

  // Initial load: On fresh application launch, clear previous sessions and reset to default.
  // On page refresh within the same active session, restore session.
  useEffect(() => {
    const initSessionsList = async () => {
      const isAppActive = sessionStorage.getItem('interview_app_active');
      if (!isAppActive) {
        // Fresh application launch: reset backend sessions to default only
        try {
          const res = await sessionsApi.reset();
          if (res.data && res.data.length > 0) {
            setSessions(res.data);
          } else {
            setSessions([{ id: 'default', name: 'Default Interview Prep' }]);
          }
        } catch (e) {
          console.log('Session reset on fresh launch error:', e);
          setSessions([{ id: 'default', name: 'Default Interview Prep' }]);
        }
        sessionStorage.clear();
        sessionStorage.setItem('interview_app_active', 'true');
        sessionStorage.setItem('interview_session_id', 'default');
        setCurrentSessionIdState('default');
        setResumeDataState(null);
        setResumeScore(null);
        setJdDataState(null);
        setMatchData(null);
        setQuestionsState([]);
      } else {
        // In-tab page refresh: fetch session list and verify active session data
        try {
          const resSessions = await sessionsApi.list();
          if (resSessions.data && resSessions.data.length > 0) {
            setSessions(resSessions.data);
          }
        } catch (e) {
          console.log('Using default session list.');
        }

        const savedSid = sessionStorage.getItem('interview_session_id') || 'default';
        const cached = getSessionCache(savedSid);
        if (cached?.resume) {
          try {
            const sessRes = await sessionsApi.get(savedSid);
            if (sessRes.data) {
              const d = sessRes.data;
              if (d.resume) setResumeDataState(d.resume);
              if (d.resume_score) setResumeScore(d.resume_score);
              if (d.jd) setJdDataState(d.jd);
              if (d.match) setMatchData(d.match);
              if (d.questions && d.questions.length > 0) setQuestionsState(d.questions);
              setSessionCache(savedSid, d);
            }
          } catch (e) {
            console.warn('Error syncing session from backend on refresh:', e);
          }
        }
      }
    };

    initSessionsList();
  }, []);

  // Session persistence across SPA route transitions
  useEffect(() => {
    // Session state is preserved in sessionStorage and synced with backend
  }, [autoClearOnClose]);

  // Reset all workspaces back to clean default session
  const resetAllSessions = async () => {
    try {
      await sessionsApi.reset();
      setSessions([{ id: 'default', name: 'Default Interview Prep' }]);
      sessionStorage.clear();
      sessionStorage.setItem('interview_app_active', 'true');
      sessionStorage.setItem('interview_session_id', 'default');
      setCurrentSessionIdState('default');
      setResumeDataState(null);
      setResumeScore(null);
      setJdDataState(null);
      setMatchData(null);
      setQuestionsState([]);
      showToast('All sessions cleared. Default workspace reset.');
    } catch (e) {
      console.error('Error resetting sessions:', e);
      showToast('Failed to reset workspaces.', 'error');
    }
  };

  const createNewSession = async (name) => {
    try {
      const res = await sessionsApi.create(name);
      setSessions((prev) => [...prev, res.data]);
      await switchSession(res.data.id);
      showToast(`Session "${name}" created.`);
      return res.data;
    } catch (err) {
      showToast('Failed to create session.', 'error');
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      await sessionsApi.delete(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      sessionStorage.removeItem(`interview_session_cache_${sessionId}`);
      sessionStorage.removeItem(`mock_interview_progress_${sessionId}`);
      
      // If deleted active session, fallback safely to another session or default
      if (currentSessionId === sessionId) {
        const nextSession = remaining.length > 0 ? remaining[0].id : 'default';
        await switchSession(nextSession);
      }
      showToast('Session and associated data deleted.');
    } catch (err) {
      console.error('Delete session error:', err);
      showToast('Failed to delete session.', 'error');
    }
  };

  // Explicitly remove/clear the active resume and reset current session completely
  const clearActiveResume = async () => {
    activeRequestRef.current += 1;
    setResumeDataState(null);
    setResumeScore(null);
    setJdDataState(null);
    setMatchData(null);
    setQuestionsState([]);
    sessionStorage.removeItem(`interview_session_cache_${currentSessionId}`);
    sessionStorage.removeItem(`mock_interview_progress_${currentSessionId}`);
    sessionStorage.removeItem('interview_session_id');

    try {
      if (currentSessionId) {
        await sessionsApi.update(currentSessionId, {
          resume: null,
          resume_score: null,
          jd: null,
          match: null,
          questions: [],
        });
      }
    } catch (e) {
      console.warn('Could not sync cleared session to backend:', e);
    }
    showToast('Active resume removed and workspace reset.');
  };

  const updateResume = async (newResume) => {
    const reqId = ++activeRequestRef.current;

    // Ensure session ID is preserved in sessionStorage
    sessionStorage.setItem('interview_session_id', currentSessionId);
    sessionStorage.removeItem(`mock_interview_progress_${currentSessionId}`);

    // 1. Immediately reset stale questions, scores, matches, and previous interview state
    setQuestionsState([]);
    setResumeScore(null);
    setMatchData(null);

    if (!newResume || typeof newResume !== 'object' || (!newResume.id && !newResume.name && (!newResume.skills || newResume.skills.length === 0))) {
      setResumeDataState(null);
      await clearActiveResume();
      return;
    }

    setResumeDataState(newResume);

    try {
      if (currentSessionId) {
        await interviewApi.clearHistory(currentSessionId);
      }
    } catch (e) {
      console.log('Error resetting session history:', e);
    }

    // 2. Trigger fresh analysis & match
    let calculatedScore = null;
    let calculatedMatch = null;
    try {
      const scoreRes = await resumeApi.analyze(newResume);
      if (reqId !== activeRequestRef.current) return;
      calculatedScore = scoreRes.data.score;
      setResumeScore(calculatedScore);

      if (jdData) {
        const matchRes = await matchApi.match(newResume, jdData);
        if (reqId !== activeRequestRef.current) return;
        calculatedMatch = matchRes.data;
        setMatchData(calculatedMatch);
      }
    } catch (err) {
      console.error('Error updating resume analysis:', err);
    }

    if (reqId !== activeRequestRef.current) return;

    // 3. Persist to backend and local session cache
    await persistToBackendAndCache(currentSessionId, {
      resume: newResume,
      resume_score: calculatedScore,
      jd: jdData,
      match: calculatedMatch,
      questions: [],
    });

    const resName = newResume?.filename || newResume?.name || 'Resume';
    showToast(`Active resume updated to "${resName}". Previous questions and interview context reset.`, 'info');
  };

  const updateJd = async (newJd) => {
    const reqId = ++activeRequestRef.current;
    setJdDataState(newJd);
    let calculatedMatch = null;

    if (!newJd) {
      setMatchData(null);
      await persistToBackendAndCache(currentSessionId, {
        jd: null,
        match: null,
      });
      return;
    }

    try {
      if (resumeData) {
        const matchRes = await matchApi.match(resumeData, newJd);
        if (reqId !== activeRequestRef.current) return;
        calculatedMatch = matchRes.data;
        setMatchData(calculatedMatch);
      }
    } catch (err) {
      console.error('Error updating JD match:', err);
    }

    if (reqId !== activeRequestRef.current) return;

    // Persist to backend and cache
    await persistToBackendAndCache(currentSessionId, {
      jd: newJd,
      match: calculatedMatch,
    });
  };

  const updateQuestions = (newQuestions) => {
    setQuestionsState(newQuestions);
    persistToBackendAndCache(currentSessionId, {
      questions: newQuestions,
    });
  };

  const addProject = async (newProj) => {
    if (!resumeData) return;
    const updatedProjects = [...(resumeData.projects || []), newProj];
    const updated = { ...resumeData, projects: updatedProjects };
    await updateResume(updated);
    showToast(`Added project: ${newProj.title}`);
  };

  const updateProject = async (index, updatedProj) => {
    if (!resumeData || !resumeData.projects) return;
    const updatedProjects = [...resumeData.projects];
    updatedProjects[index] = updatedProj;
    const updated = { ...resumeData, projects: updatedProjects };
    await updateResume(updated);
    showToast(`Updated project: ${updatedProj.title}`);
  };

  const deleteProject = async (index) => {
    if (!resumeData || !resumeData.projects) return;
    const deletedTitle = resumeData.projects[index]?.title || 'Project';
    const updatedProjects = resumeData.projects.filter((_, i) => i !== index);
    const updated = { ...resumeData, projects: updatedProjects };
    await updateResume(updated);
    showToast(`Deleted ${deletedTitle}`);
  };

  return (
    <SessionContext.Provider
      value={{
        sessions,
        currentSessionId,
        setCurrentSessionId: switchSession,
        createNewSession,
        deleteSession,
        autoClearOnClose,
        setAutoClearOnClose,
        resumeData,
        setResumeData: updateResume,
        clearActiveResume,
        resumeScore,
        setResumeScore,
        jdData,
        setJdData: updateJd,
        matchData,
        setMatchData,
        questions,
        setQuestions: updateQuestions,
        clearSessionHistory,
        resetAllSessions,
        addProject,
        updateProject,
        deleteProject,
        loadSampleData,
        loading,
        toast,
        showToast,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => useContext(SessionContext);


