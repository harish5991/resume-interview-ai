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
  Plus,
  Edit2,
  Trash2,
  CheckCircle2,
  Copy,
  Check,
  ArrowRight,
  Code2,
  Sparkles,
  X
} from 'lucide-react';
import { Badge } from '../components/common/Badge';

export const ProjectDeepDive = () => {
  const navigate = useNavigate();
  const { resumeData, addProject, updateProject, deleteProject, showToast } = useSession();
  
  const [selectedProjectIndex, setSelectedProjectIndex] = useState(0);
  const [deepDiveData, setDeepDiveData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Modal State for Add / Edit Project
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null); // null = Add, number = Edit
  const [formTitle, setFormTitle] = useState('');
  const [formTech, setFormTech] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formBullets, setFormBullets] = useState('');

  const projects = resumeData?.projects || [];
  const currentProject = projects[selectedProjectIndex] || projects[0];

  useEffect(() => {
    if (currentProject) {
      setLoading(true);
      interviewApi
        .getProjectDeepDive(
          currentProject.title,
          currentProject.technologies || [],
          currentProject.description || currentProject.highlights?.join(' ') || ''
        )
        .then((res) => {
          setDeepDiveData(res.data);
        })
        .catch((err) => {
          console.error(err);
          // Fallback deep dive data
          setDeepDiveData({
            project_name: currentProject.title,
            objective: currentProject.description || "Production-grade system implementation.",
            technologies: currentProject.technologies || ["Python", "FastAPI", "React"],
            architecture: `Layered microservice architecture separating ingestion, business processing, and client presentation. Implemented ${currentProject.technologies?.[0] || 'core technologies'} with async task execution.`,
            database_choice: `Primary storage selected for low latency and high consistency, with compound indexing on query lookup paths.`,
            apis_design: `Standardized RESTful JSON endpoints with strict Pydantic payload validation, CORS policies, and rate limiting.`,
            challenges_solutions: `Mitigated processing latency and memory bottlenecks by introducing batch processing and connection pooling.`,
            security_aspects: `Applied input sanitization, JWT authorization bearer tokens, and non-root container isolation.`,
            scalability_notes: `Horizontal pod autoscaling on Kubernetes with Redis cache offloading.`,
            interview_questions: [
              {
                id: `proj-q-1`,
                question: `How did you architect the end-to-end data pipeline in ${currentProject.title}?`,
                difficulty: "Medium",
                skill: currentProject.technologies?.[0] || "Architecture",
                why_this_question: "Tests system design clarity and end-to-end component ownership.",
                expected_answer_points: ["Component separation", "Data ingestion flow", "Bottleneck mitigation"],
                sample_answer: `In ${currentProject.title}, I designed the pipeline with decoupled services where raw inputs are validated, preprocessed asynchronously, and routed to the core processing engine. We minimized latency by implementing connection pooling and in-memory caching.`
              },
              {
                id: `proj-q-2`,
                question: `What was the primary technical trade-off you encountered when using ${currentProject.technologies?.[1] || currentProject.technologies?.[0] || 'these tools'}?`,
                difficulty: "Hard",
                skill: currentProject.technologies?.[1] || "Engineering Trade-offs",
                why_this_question: "Assesses senior engineering judgment under production constraints.",
                expected_answer_points: ["Memory vs CPU trade-off", "Consistency vs Availability", "Alternative tools evaluated"],
                sample_answer: `The primary trade-off was throughput versus resource consumption. We initially tested a synchronous architecture, but shifted to an asynchronous pipeline to prevent thread blocking during peak load.`
              }
            ]
          });
        })
        .finally(() => setLoading(false));
    } else {
      setDeepDiveData(null);
    }
  }, [selectedProjectIndex, resumeData]);

  const handleOpenAddModal = () => {
    setEditingIndex(null);
    setFormTitle('');
    setFormTech('');
    setFormDesc('');
    setFormBullets('');
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (idx) => {
    const proj = projects[idx];
    if (!proj) return;
    setEditingIndex(idx);
    setFormTitle(proj.title || '');
    setFormTech((proj.technologies || []).join(', '));
    setFormDesc(proj.description || '');
    setFormBullets((proj.highlights || []).join('\n'));
    setIsModalOpen(true);
  };

  const handleSaveProject = async (e) => {
    e.preventDefault();
    if (!formTitle.trim()) {
      showToast('Project title is required.', 'warning');
      return;
    }

    const techList = formTech
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const highlightsList = formBullets
      .split('\n')
      .map((b) => b.trim().replace(/^[•\-*]\s*/, ''))
      .filter((b) => b.length > 0);

    const projectPayload = {
      title: formTitle.trim(),
      description: formDesc.trim() || `Technical implementation focusing on ${techList.slice(0, 3).join(', ')}.`,
      technologies: techList.length > 0 ? techList : ['Python', 'FastAPI'],
      highlights: highlightsList.length > 0 ? highlightsList : [`Engineered core features using ${techList[0] || 'Python'}.`]
    };

    if (editingIndex !== null) {
      await updateProject(editingIndex, projectPayload);
    } else {
      await addProject(projectPayload);
      setSelectedProjectIndex(projects.length); // Select newly added project
    }

    setIsModalOpen(false);
  };

  const handleDeleteProject = async (idx) => {
    if (window.confirm(`Are you sure you want to delete "${projects[idx]?.title}"?`)) {
      await deleteProject(idx);
      setSelectedProjectIndex(Math.max(0, idx - 1));
    }
  };

  const handleCopyAnswer = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
    showToast('Suggested answer copied to clipboard.');
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Title & Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-xs">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">Project Dashboard</h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Architectural blueprints, technology stacks, and interview question preparation for all {projects.length} detected projects.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleOpenAddModal}
            className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Project</span>
          </button>
        </div>
      </div>

      {/* Project Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2 bg-slate-100/70 p-1.5 rounded-xl border border-slate-200/80">
        {projects.map((p, idx) => (
          <div
            key={idx}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
              selectedProjectIndex === idx
                ? 'bg-white text-blue-900 shadow-sm border border-slate-200'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
            }`}
          >
            <button
              onClick={() => setSelectedProjectIndex(idx)}
              className="flex items-center gap-1.5 text-left"
            >
              <Code2 className={`w-3.5 h-3.5 ${selectedProjectIndex === idx ? 'text-blue-600' : 'text-slate-400'}`} />
              <span className="font-bold">{p.title}</span>
              <span className="text-[10px] px-1.5 py-0.2 bg-slate-100 rounded text-slate-500 font-normal">
                {p.technologies?.length || 0} tech
              </span>
            </button>
            <button
              onClick={() => handleOpenEditModal(idx)}
              className="text-slate-400 hover:text-blue-600 p-0.5 rounded transition-colors ml-1"
              title="Edit Project"
            >
              <Edit2 className="w-3 h-3" />
            </button>
            {projects.length > 1 && (
              <button
                onClick={() => handleDeleteProject(idx)}
                className="text-slate-400 hover:text-rose-600 p-0.5 rounded transition-colors"
                title="Delete Project"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}

        <button
          onClick={handleOpenAddModal}
          className="flex items-center gap-1 px-3 py-2 text-xs font-semibold text-blue-600 hover:text-blue-800 hover:bg-blue-50/50 rounded-lg transition-colors ml-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Another Project</span>
        </button>
      </div>

      {/* Main Content Area */}
      {currentProject ? (
        <div className="space-y-6">
          {/* Active Project Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-slate-900">{currentProject.title}</h2>
                  <Badge variant="primary" size="xs">Active Project #{selectedProjectIndex + 1}</Badge>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed max-w-4xl">
                  {currentProject.description || "Comprehensive software engineering project implementation."}
                </p>
              </div>

              <div className="flex flex-wrap gap-1.5 sm:justify-end">
                {currentProject.technologies?.map((tech, tidx) => (
                  <Badge key={tidx} variant="neutral" size="sm">
                    {tech}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Bullet Highlights */}
            {currentProject.highlights && currentProject.highlights.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                  Documented Achievements & Highlights
                </span>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-700">
                  {currentProject.highlights.map((h, hidx) => (
                    <li key={hidx} className="flex items-start gap-2 p-2 bg-slate-50 rounded-lg border border-slate-100">
                      <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Architectural Blueprint Dossier */}
          {loading ? (
            <div className="p-12 text-center bg-white rounded-xl border border-slate-200 space-y-2">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent" />
              <p className="text-xs text-slate-600 font-medium">Generating deep architectural breakdown...</p>
            </div>
          ) : deepDiveData ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  Architectural Dossier & System Design
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                    <div className="p-1.5 bg-blue-50 text-blue-700 rounded-md">
                      <Cpu className="w-4 h-4" />
                    </div>
                    <span>System Architecture</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.architecture}</p>
                </div>

                <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                    <div className="p-1.5 bg-emerald-50 text-emerald-700 rounded-md">
                      <Database className="w-4 h-4" />
                    </div>
                    <span>Database & Persistence</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.database_choice}</p>
                </div>

                <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                    <div className="p-1.5 bg-purple-50 text-purple-700 rounded-md">
                      <Terminal className="w-4 h-4" />
                    </div>
                    <span>API & Communication</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.apis_design}</p>
                </div>

                <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                    <div className="p-1.5 bg-amber-50 text-amber-700 rounded-md">
                      <Zap className="w-4 h-4" />
                    </div>
                    <span>Engineering Challenges</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.challenges_solutions}</p>
                </div>

                <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                    <div className="p-1.5 bg-rose-50 text-rose-700 rounded-md">
                      <Shield className="w-4 h-4" />
                    </div>
                    <span>Security & Resilience</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.security_aspects}</p>
                </div>

                <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                    <div className="p-1.5 bg-indigo-50 text-indigo-700 rounded-md">
                      <GitBranch className="w-4 h-4" />
                    </div>
                    <span>Scale & Concurrency</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{deepDiveData.scalability_notes}</p>
                </div>
              </div>

              {/* Grounded Project Interview Questions */}
              <div className="space-y-3 pt-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                    Project-Specific Interview Questions ({deepDiveData.interview_questions?.length || 0})
                  </h3>
                  <span className="text-[11px] text-slate-500">Grounded in your project's technology choices</span>
                </div>

                <div className="space-y-3">
                  {deepDiveData.interview_questions?.map((q, idx) => (
                    <div key={idx} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1.5 flex-1">
                          <div className="flex items-center gap-2">
                            <Badge variant={q.difficulty.toLowerCase()} size="xs">{q.difficulty}</Badge>
                            <Badge variant="primary" size="xs">{q.skill}</Badge>
                          </div>
                          <h4 className="text-sm font-bold text-slate-900">{q.question}</h4>
                        </div>

                        <button
                          onClick={() => navigate('/mock-interview', { state: { selectedQuestion: q } })}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors flex-shrink-0"
                        >
                          <Mic className="w-3.5 h-3.5" />
                          <span>Practice in Mock Interview</span>
                        </button>
                      </div>

                      {q.why_this_question && (
                        <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                          <span className="font-semibold text-slate-800 mr-1">Interviewer Intent:</span>
                          {q.why_this_question}
                        </p>
                      )}

                      {/* Expected Talking Points */}
                      {q.expected_answer_points && q.expected_answer_points.length > 0 && (
                        <div className="text-[11px] text-slate-600 flex flex-wrap items-center gap-1.5">
                          <span className="font-semibold text-slate-800 mr-1">Checkpoints:</span>
                          {q.expected_answer_points.map((pt, pidx) => (
                            <span key={pidx} className="inline-flex items-center bg-slate-100 px-2 py-0.5 rounded border border-slate-200 text-slate-700">
                              {pt}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Suggested Answer Preview */}
                      {q.sample_answer && (
                        <div className="pt-2 border-t border-slate-100 space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wide">
                              Suggested Model Answer
                            </span>
                            <button
                              onClick={() => handleCopyAnswer(q.sample_answer, idx)}
                              className="flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-2 py-0.5 rounded transition-colors"
                            >
                              {copiedIndex === idx ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                              <span>{copiedIndex === idx ? 'Copied' : 'Copy Answer'}</span>
                            </button>
                          </div>
                          <p className="text-xs text-slate-700 leading-relaxed bg-slate-50/70 p-3 rounded-lg border border-slate-200/80">
                            {q.sample_answer}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 space-y-3">
          <Layers className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">No Projects Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Upload your resume or click the button below to add your projects manually.
          </p>
          <button
            onClick={handleOpenAddModal}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors inline-flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add First Project</span>
          </button>
        </div>
      )}

      {/* Add / Edit Project Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full p-6 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                  {editingIndex !== null ? <Edit2 className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                </div>
                <h3 className="font-bold text-slate-900 text-base">
                  {editingIndex !== null ? 'Edit Project' : 'Add New Project'}
                </h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveProject} className="space-y-4">
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-700">
                  Project Title <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  placeholder="e.g. Smart Traffic Management System"
                  required
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-700">
                  Technologies / Frameworks <span className="text-slate-400 font-normal">(comma-separated)</span>
                </label>
                <input
                  type="text"
                  value={formTech}
                  onChange={(e) => setFormTech(e.target.value)}
                  placeholder="e.g. Python, YOLOv8, OpenCV, FastAPI, Docker"
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-700">
                  Project Description / Objective
                </label>
                <textarea
                  rows={2}
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  placeholder="Brief summary of what the project achieves and why it was built..."
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-700">
                  Key Achievements / Highlights <span className="text-slate-400 font-normal">(one per line)</span>
                </label>
                <textarea
                  rows={3}
                  value={formBullets}
                  onChange={(e) => setFormBullets(e.target.value)}
                  placeholder="• Developed real-time vehicle detection with YOLOv8 at 38 FPS.&#10;• Reduced latency by 35% with OpenCV ROI masking."
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
                >
                  {editingIndex !== null ? 'Save Changes' : 'Add Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
