import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SessionProvider, useSession } from './context/SessionContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { Toast } from './components/common/Toast';

import { Home } from './pages/Home';
import { ResumeAnalysis } from './pages/ResumeAnalysis';
import { JobMatch } from './pages/JobMatch';
import { GenerateQuestions } from './pages/GenerateQuestions';
import { MockInterview } from './pages/MockInterview';
import { SkillGap } from './pages/SkillGap';
import { ProjectDeepDive } from './pages/ProjectDeepDive';
import { PreparationMode } from './pages/PreparationMode';
import { ResumeImprovement } from './pages/ResumeImprovement';
import { AnalyticsDashboard } from './pages/AnalyticsDashboard';
import { SavedQuestions } from './pages/SavedQuestions';
import { QuestionHistory } from './pages/QuestionHistory';

const AppLayout = () => {
  const { toast } = useSession();

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
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
