import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { interviewApi } from '../services/api';
import {
  Layers,
  Cpu,
  Database,
  Shield,
  Zap,
  Mic,
  GitBranch,
  Terminal,
  ArrowLeft
} from 'lucide-react';
import { Badge } from '../components/common/Badge';

export const ProjectDeepDive = () => {
  const navigate = useNavigate();
  const { resumeData, showToast } = useSession();
  const [selectedProjectIndex, setSelectedProjectIndex] = useState(0);
  const [deepDiveData, setDeepDiveData] = useState(null);
  const [loading, setLoading] = useState(false);

  const projects = resumeData?.projects || [];
  const currentProject = projects[selectedProjectIndex];

  useEffect(() => {
    if (currentProject) {
      setLoading(true);
      interviewApi
        .getProjectDeepDive(
          currentProject.title,
          currentProject.technologies,
          currentProject.description || currentProject.highlights?.join(' ')
        )
        .then((res) => {
          setDeepDiveData(res.data);
        })
        .catch((err) => {
          console.error(err);
          showToast('Failed to load project deep-dive analysis.', 'error');
        })
        .finally(() => setLoading(false));
    }
  }, [selectedProjectIndex, resumeData]);

  return (
    <div className="space-y-6 pb-12">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/resume')}
              className="text-slate-400 hover:text-slate-600 p-1 rounded transition-colors"
              title="Back to Resume"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Project Deep-Dive</h1>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 ml-6">
            Architectural analysis and project-specific interview questions.
          </p>
        </div>

        <button
          onClick={() => navigate('/resume')}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
        >
          View Full Resume Analysis
        </button>
      </div>

      {/* Project Selector Tabs */}
      {projects.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {projects.map((p, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedProjectIndex(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors flex items-center gap-1.5 ${
                selectedProjectIndex === idx
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>{p.title}</span>
            </button>
          ))}
        </div>
      ) : (
        <div className="p-8 bg-white rounded-xl border border-slate-200 text-center text-xs text-slate-500">
          No projects found in uploaded resume.
        </div>
      )}

      {/* Deep Dive Dossier */}
      {deepDiveData && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900">{deepDiveData.project_name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">{deepDiveData.objective}</p>
              </div>
              <div className="flex flex-wrap gap-1">
                {deepDiveData.technologies?.map((t, idx) => (
                  <Badge key={idx} variant="primary" size="xs">
                    {t}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Cpu className="w-3.5 h-3.5 text-slate-600" />
                  <span>Architecture</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.architecture}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Database className="w-3.5 h-3.5 text-slate-600" />
                  <span>Database Choice</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.database_choice}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Terminal className="w-3.5 h-3.5 text-slate-600" />
                  <span>API Design</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.apis_design}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Zap className="w-3.5 h-3.5 text-slate-600" />
                  <span>Key Challenge</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.challenges_solutions}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Shield className="w-3.5 h-3.5 text-slate-600" />
                  <span>Security</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.security_aspects}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <GitBranch className="w-3.5 h-3.5 text-slate-600" />
                  <span>Scale Strategy</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.scalability_notes}</p>
              </div>
            </div>
          </div>

          {/* Hard Questions */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Project Interview Questions ({deepDiveData.interview_questions?.length || 0})
            </h3>

            <div className="space-y-2.5">
              {deepDiveData.interview_questions?.map((q, idx) => (
                <div key={idx} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-1.5">
                        <Badge variant={q.difficulty.toLowerCase()} size="xs">{q.difficulty}</Badge>
                        <Badge variant="primary" size="xs">{q.skill}</Badge>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">{q.question}</h4>
                    </div>

                    <button
                      onClick={() => navigate('/mock-interview', { state: { selectedQuestion: q } })}
                      className="flex items-center gap-1 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-md transition-colors flex-shrink-0"
                    >
                      <Mic className="w-3 h-3 text-slate-600" />
                      <span>Practice</span>
                    </button>
                  </div>

                  <p className="text-xs text-slate-500">
                    <b>Rationale:</b> {q.why_this_question}
                  </p>

                  {q.expected_answer_points && (
                    <div className="pt-2 border-t border-slate-100 text-xs text-slate-600 space-y-0.5">
                      <span className="font-semibold text-slate-700">Expected Talking Points:</span>
                      <ul className="space-y-0.5 pl-2">
                        {q.expected_answer_points.map((pt, pidx) => (
                          <li key={pidx} className="flex items-start gap-1">
                            <span className="text-blue-500 font-bold">•</span>
                            <span>{pt}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
