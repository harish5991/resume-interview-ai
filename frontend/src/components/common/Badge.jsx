import React from 'react';

export const Badge = ({ children, variant = 'default', size = 'sm', className = '' }) => {
  const base = "inline-flex items-center font-medium rounded-md transition-colors";
  
  const sizeClasses = {
    xs: "px-1.5 py-0.5 text-[11px] leading-tight",
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs"
  };

  const variants = {
    default: "bg-slate-100 text-slate-700 border border-slate-200/80",
    primary: "bg-blue-50 text-blue-700 border border-blue-200/70",
    success: "bg-emerald-50 text-emerald-700 border border-emerald-200/70",
    warning: "bg-amber-50 text-amber-800 border border-amber-200/70",
    danger: "bg-rose-50 text-rose-700 border border-rose-200/70",
    purple: "bg-indigo-50 text-indigo-700 border border-indigo-200/70",
    easy: "bg-emerald-50 text-emerald-700 border border-emerald-200/70",
    medium: "bg-amber-50 text-amber-800 border border-amber-200/70",
    hard: "bg-rose-50 text-rose-700 border border-rose-200/70",
    expert: "bg-indigo-50 text-indigo-700 border border-indigo-200/70",
    neutral: "bg-slate-50 text-slate-600 border border-slate-200"
  };

  const variantKey = variant ? variant.toLowerCase() : 'default';
  const appliedVariant = variants[variantKey] || variants.default;

  return (
    <span className={`${base} ${sizeClasses[size] || sizeClasses.sm} ${appliedVariant} ${className}`}>
      {children}
    </span>
  );
};

