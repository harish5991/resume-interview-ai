import React, { createContext, useContext, useState, useEffect } from 'react';
import { sessionsApi, resumeApi, jobApi, matchApi } from '../services/api';
import { FALLBACK_RESUMES, FALLBACK_JDS } from '../utils/fallbackData';

const SessionContext = createContext();

export const SessionProvider = ({ children }) => {
  const [sessions, setSessions] = useState([{ id: 'default', name: 'Default Interview Prep' }]);
  
  // Use sessionStorage so that closing the tab/window resets the session and clears question history
  const [currentSessionId, setCurrentSessionId] = useState(() => {
    let sid = sessionStorage.getItem('interview_session_id');
    if (!sid) {
      sid = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8);
      sessionStorage.setItem('interview_session_id', sid);
    }
    return sid;
  });

  const [resumeData, setResumeData] = useState(FALLBACK_RESUMES[0]);
  const [resumeScore, setResumeScore] = useState(null);
  const [jdData, setJdData] = useState(FALLBACK_JDS[0]);
  const [matchData, setMatchData] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type, id: Date.now() });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  const clearSessionHistory = async () => {
    try {
      await interviewApi.clearHistory(currentSessionId);
      showToast('Question and interview history cleared.');
    } catch (e) {
      console.log('Error clearing history:', e);
    }
  };

  // Initial load
  useEffect(() => {
    const initSession = async () => {
      try {
        // Try fetching sessions list
        try {
          const resSessions = await sessionsApi.list();
          if (resSessions.data && resSessions.data.length > 0) {
            setSessions(resSessions.data);
          }
        } catch (e) {
          console.log('Using default session list.');
        }

        // Try fetching sample data from API
        let defaultResume = FALLBACK_RESUMES[0];
        let defaultJd = FALLBACK_JDS[0];

        try {
          const sampleRes = await resumeApi.getSamples();
          if (sampleRes.data && sampleRes.data.length > 0) {
            defaultResume = sampleRes.data[0];
          }
        } catch (e) {
          console.log('Using fallback demo resume.');
        }

        try {
          const sampleJds = await jobApi.getSamples();
          if (sampleJds.data && sampleJds.data.length > 0) {
            defaultJd = sampleJds.data[0];
          }
        } catch (e) {
          console.log('Using fallback demo JD.');
        }

        setResumeData(defaultResume);
        setJdData(defaultJd);

        // Calculate initial match & score
        if (defaultResume) {
          try {
            const scoreRes = await resumeApi.analyze(defaultResume);
            setResumeScore(scoreRes.data.score);
          } catch (e) {
            console.log('Calculated local resume score fallback.');
          }
        }

        if (defaultResume && defaultJd) {
          try {
            const matchRes = await matchApi.match(defaultResume, defaultJd);
            setMatchData(matchRes.data);
          } catch (e) {
            console.log('Calculated local match fallback.');
          }
        }
      } catch (err) {
        console.error('Initialization error:', err);
      }
    };

    initSession();
  }, []);

  const createNewSession = async (name) => {
    try {
      const res = await sessionsApi.create(name);
      setSessions((prev) => [...prev, res.data]);
      setCurrentSessionId(res.data.id);
      showToast(`Session "${name}" created.`);
      return res.data;
    } catch (err) {
      showToast('Failed to create session.', 'error');
    }
  };

  const updateResume = async (newResume) => {
    setResumeData(newResume);
    try {
      const scoreRes = await resumeApi.analyze(newResume);
      setResumeScore(scoreRes.data.score);
      if (jdData) {
        const matchRes = await matchApi.match(newResume, jdData);
        setMatchData(matchRes.data);
      }
    } catch (err) {
      console.error('Error updating resume analysis:', err);
    }
  };

  const updateJd = async (newJd) => {
    setJdData(newJd);
    try {
      if (resumeData) {
        const matchRes = await matchApi.match(resumeData, newJd);
        setMatchData(matchRes.data);
      }
    } catch (err) {
      console.error('Error updating JD match:', err);
    }
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
        setCurrentSessionId,
        resumeData,
        setResumeData: updateResume,
        resumeScore,
        setResumeScore,
        jdData,
        setJdData: updateJd,
        matchData,
        setMatchData,
        questions,
        setQuestions,
        createNewSession,
        clearSessionHistory,
        addProject,
        updateProject,
        deleteProject,
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
