import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Layers,
  Target,
  HelpCircle,
  Mic,
  GitPullRequest,
  BarChart3,
  BookmarkCheck,
  History,
  Sliders,
  Briefcase
} from 'lucide-react';
import { useSession } from '../../context/SessionContext';

export const Sidebar = () => {
  const { currentSessionId } = useSession();

  const workspaceNav = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
    { to: "/resume", label: "Resume", icon: FileText },
    { to: "/projects", label: "Project Dashboard", icon: Layers },
    { to: "/match", label: "Job Match", icon: Target },
    { to: "/questions", label: "Questions", icon: HelpCircle },
    { to: "/mock-interview", label: "Mock Interview", icon: Mic },
  ];

  const insightsNav = [
    { to: "/skill-gap", label: "Skill Gaps", icon: GitPullRequest },
    { to: "/analytics", label: "Analytics", icon: BarChart3 },
    { to: "/saved", label: "Saved Questions", icon: BookmarkCheck },
    { to: "/history", label: "Question History", icon: History },
  ];

  return (
    <aside className="w-60 bg-white border-r border-slate-200 flex flex-col h-screen sticky top-0 select-none z-20 flex-shrink-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-100 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white shadow-sm">
          <Briefcase className="w-4 h-4 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-slate-900 leading-none text-sm">Resume Interview</h1>
          <span className="text-[11px] text-slate-500 font-medium">Prep Workspace</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {/* Workspace */}
        <div className="space-y-1">
          <div className="px-2 pb-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Workspace
          </div>
          {workspaceNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-100 text-slate-900 font-semibold'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0 text-slate-500" />
                <span className="flex-1 truncate">{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        {/* Insights */}
        <div className="space-y-1">
          <div className="px-2 pb-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Insights
          </div>
          {insightsNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-100 text-slate-900 font-semibold'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0 text-slate-500" />
                <span className="flex-1 truncate">{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        {/* Settings / Info */}
        <div className="space-y-1">
          <div className="px-2 pb-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Settings
          </div>
          <NavLink
            to="/history"
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-slate-100 text-slate-900 font-semibold'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            <Sliders className="w-4 h-4 flex-shrink-0 text-slate-500" />
            <span className="flex-1 truncate">Session & Preferences</span>
          </NavLink>
        </div>
      </nav>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/70">
        <div className="text-[11px] text-slate-500 flex items-center justify-between">
          <span className="truncate max-w-[120px]" title={currentSessionId}>
            {currentSessionId === 'default' ? 'Default Session' : 'Active Session'}
          </span>
          <span className="font-medium text-emerald-700 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Ready
          </span>
        </div>
      </div>
    </aside>
  );
};
