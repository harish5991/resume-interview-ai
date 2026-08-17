import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SessionProvider, useSession } from './context/SessionContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { Toast } from './components/common/Toast';
import { ErrorBoundary } from './components/common/ErrorBoundary';

import { Home } from './pages/Home';

const ResumeAnalysis = lazy(() => import('./pages/ResumeAnalysis').then(m => ({ default: m.ResumeAnalysis })));
const JobMatch = lazy(() => import('./pages/JobMatch').then(m => ({ default: m.JobMatch })));
const GenerateQuestions = lazy(() => import('./pages/GenerateQuestions').then(m => ({ default: m.GenerateQuestions })));
const MockInterview = lazy(() => import('./pages/MockInterview').then(m => ({ default: m.MockInterview })));
const SkillGap = lazy(() => import('./pages/SkillGap').then(m => ({ default: m.SkillGap })));
const ProjectDeepDive = lazy(() => import('./pages/ProjectDeepDive').then(m => ({ default: m.ProjectDeepDive })));
const PreparationMode = lazy(() => import('./pages/PreparationMode').then(m => ({ default: m.PreparationMode })));
const ResumeImprovement = lazy(() => import('./pages/ResumeImprovement').then(m => ({ default: m.ResumeImprovement })));
const AnalyticsDashboard = lazy(() => import('./pages/AnalyticsDashboard').then(m => ({ default: m.AnalyticsDashboard })));
const SavedQuestions = lazy(() => import('./pages/SavedQuestions').then(m => ({ default: m.SavedQuestions })));
const QuestionHistory = lazy(() => import('./pages/QuestionHistory').then(m => ({ default: m.QuestionHistory })));

const RouteLoading = () => (
  <div className="flex items-center justify-center min-h-[50vh]">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
      <span className="text-xs text-slate-500 font-medium">Loading workspace module...</span>
    </div>
  </div>
);

const AppLayout = () => {
  const { toast } = useSession();

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <ErrorBoundary>
            <Suspense fallback={<RouteLoading />}>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/resume" element={<ResumeAnalysis />} />
                <Route path="/match" element={<JobMatch />} />
                <Route path="/questions" element={<GenerateQuestions />} />
                <Route path="/mock-interview" element={<MockInterview />} />
                <Route path="/skill-gap" element={<SkillGap />} />
                <Route path="/projects" element={<ProjectDeepDive />} />
                <Route path="/prep" element={<PreparationMode />} />
                <Route path="/improve" element={<ResumeImprovement />} />
                <Route path="/analytics" element={<AnalyticsDashboard />} />
                <Route path="/saved" element={<SavedQuestions />} />
                <Route path="/history" element={<QuestionHistory />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
      <Toast toast={toast} />
    </div>
  );
};

export default function App() {
  return (
    <SessionProvider>
      <Router>
        <AppLayout />
      </Router>
    </SessionProvider>
  );
}
