import React from "react";

export const ProgressBar: React.FC<{ progress: number; label?: string }> = ({
  progress,
  label
}) => {
  const bounded = Math.min(100, Math.max(0, progress));
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between text-xs text-slate-400 mb-1">
          <span>{label}</span>
          <span>{bounded}%</span>
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={bounded}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuetext={`${bounded}%`}
        className="w-full bg-slate-800 h-2 rounded-full overflow-hidden"
      >
        <div
          className="bg-blue-500 h-full transition-all duration-300 ease-out"
          style={{ width: `${bounded}%` }}
        />
      </div>
    </div>
  );
};
