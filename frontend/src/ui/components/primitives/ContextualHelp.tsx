import React, { useState, useId } from "react";
import { CancelXIcon, CircleHelpIcon } from "../../icons/index";

export interface ContextualHelpProps {
  title: string;
  content: string;
  icon?: React.ReactNode;
}

export const ContextualHelp: React.FC<ContextualHelpProps> = ({
  title,
  content,
  icon
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const helpId = useId().replace(/:/g, "");

  return (
    <div className="inline-block relative">
      <button
        type="button"
        aria-label={`Ver ayuda contextual: ${title}`}
        aria-expanded={isOpen}
        aria-controls={`help-content-${helpId}`}
        onClick={() => setIsOpen(!isOpen)}
        className="p-1 rounded-lg text-slate-400 hover:text-blue-400 hover:bg-slate-800 transition focus-visible:ring-2 focus-visible:ring-blue-500"
      >
        {icon ?? <CircleHelpIcon size={16} />}
      </button>
      {isOpen && (
        <div
          id={`help-content-${helpId}`}
          role="region"
          className="absolute z-40 mt-1 w-72 p-3 bg-slate-900 border border-slate-700 rounded-xl shadow-xl text-left text-xs text-slate-300"
        >
          <div className="flex justify-between items-center pb-1 mb-1 border-b border-slate-800">
            <span className="font-semibold text-white">{title}</span>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white"
              aria-label="Cerrar ayuda"
            >
              <CancelXIcon size={12} />
            </button>
          </div>
          <p>{content}</p>
        </div>
      )}
    </div>
  );
};
