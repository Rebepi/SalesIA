import React, { useState, useRef, useEffect } from "react";

export const Popover: React.FC<{ trigger: React.ReactNode; content: React.ReactNode }> = ({
  trigger,
  content
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  return (
    <div className="relative inline-block" ref={popoverRef}>
      <div
        role="button"
        tabIndex={0}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setIsOpen(!isOpen);
          }
        }}
      >
        {trigger}
      </div>
      {isOpen && (
        <div
          role="dialog"
          className="absolute top-full left-0 mt-2 p-4 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 min-w-[200px] text-sm animate-in fade-in"
        >
          {content}
        </div>
      )}
    </div>
  );
};
