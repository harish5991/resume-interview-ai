import axios from 'axios';

const RAW_API_URL = import.meta.env.VITE_API_URL || '';
export const API_BASE_URL = RAW_API_URL ? `${RAW_API_URL.replace(/\/+$/, '')}/api` : '/api';
export const HEALTH_CHECK_URL = RAW_API_URL ? `${RAW_API_URL.replace(/\/+$/, '')}/api/health` : '/health';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Intercept 502 / network connection errors with friendly message
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 502 || error.response?.status === 503 || error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
      const friendlyDetail = 'Backend server is not running on http://127.0.0.1:8000. Please start the backend with "run.bat" or "python run.py".';
      if (error.response?.data) {
        error.response.data.detail = friendlyDetail;
      } else {
        error.response = {
          status: 502,
          data: { detail: friendlyDetail }
        };
      }
    }
    return Promise.reject(error);
  }
);

export const resumeApi = {
  getSamples: () => api.get('/resume/samples'),
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  analyze: (resumeData) => api.post('/resume/analyze', resumeData),
};

export const jobApi = {
  getSamples: () => api.get('/job/samples'),
  analyze: (text) => api.post('/job/analyze', { text }),
};

export const matchApi = {
  match: (resume, jd) => api.post('/match', { resume, jd }),
};

export const questionsApi = {
  generate: (payload) => api.post('/questions/generate', payload),
  regenerate: (payload) => api.post('/questions/regenerate', payload),
  toggleBookmark: (question, sessionId = 'default') =>
    api.post('/questions/bookmark', { question, session_id: sessionId }),
  getSaved: (sessionId = 'default') =>
    api.get(`/questions/saved?session_id=${sessionId}`),
};

export const interviewApi = {
  evaluateAnswer: (payload) => api.post('/interview/answer', payload),
  getFinalEvaluation: (payload) => api.post('/interview/final-evaluation', payload),
  getHistory: (sessionId = 'default') =>
    api.get(`/interview/history?session_id=${sessionId}`),
  clearHistory: (sessionId = 'default') =>
    api.delete(`/interview/history?session_id=${sessionId}`),
  getProjectDeepDive: (title, technologies, description) =>
    api.post('/interview/project-deep-dive', {
      title,
      technologies,
      description,
    }),
  getTopics: (resume, jd) => api.post('/interview/topics', { resume, jd }),
};

export const analyticsApi = {
  getAnalytics: (sessionId = 'default') =>
    api.get(`/analytics?session_id=${sessionId}`),
  getSkillGap: (resume, jd) => api.post('/analytics/skill-gap', { resume, jd }),
  getImprovements: (resume) =>
    api.post('/analytics/improvements', { resume }),
};

export const reportApi = {
  exportPdf: (sessionId = 'default', extraData = {}) =>
    api.post(
      '/report/export',
      { session_id: sessionId, ...extraData },
      { responseType: 'blob' }
    ),
};

export const sessionsApi = {
  list: () => api.get('/sessions'),
  create: (name) => api.post('/sessions', { name }),
  get: (id) => api.get(`/sessions/${id}`),
  update: (id, data) => api.put(`/sessions/${id}`, data),
  delete: (id) => api.delete(`/sessions/${id}`),
  reset: () => api.post('/sessions/reset'),
  resetUrl: `${API_BASE_URL}/sessions/reset`,
};

export default api;
