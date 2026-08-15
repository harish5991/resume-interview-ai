import React from 'react';

export const ScoreRing = ({ score = 0, size = 80, strokeWidth = 6, label = "Score", color }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.min(100, Math.max(0, Math.round(score)));
  const offset = circumference - (clampedScore / 100) * circumference;

  let strokeColor = color;
  if (!strokeColor) {
    if (clampedScore >= 80) strokeColor = "#16a34a"; // Green/Emerald
    else if (clampedScore >= 65) strokeColor = "#2563eb"; // Blue
    else if (clampedScore >= 50) strokeColor = "#d97706"; // Amber
    else strokeColor = "#dc2626"; // Rose/Red
  }

  return (
    <div className="flex flex-col items-center justify-center relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#f1f5f9"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-base font-bold text-slate-900 tracking-tight leading-none">
          {clampedScore}%
        </span>
        {label && <span className="text-[10px] text-slate-500 font-medium mt-0.5 uppercase tracking-wider">{label}</span>}
      </div>
    </div>
  );
};

