import React, { useState, useRef, useEffect } from "react";

export interface DropdownMenuItem {
  label: string;
  onClick: () => void;
  icon?: React.ReactNode;
  danger?: boolean;
  isSeparator?: boolean;
}

export const DropdownMenu: React.FC<{
  trigger: React.ReactNode;
  items: DropdownMenuItem[];
}> = ({ trigger, items }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setIsOpen(true);
      setActiveIndex((prev) => (prev < items.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setIsOpen(true);
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : items.length - 1));
    } else if (e.key === "Enter" || e.key === " ") {
      if (isOpen && activeIndex >= 0 && items[activeIndex]) {
        e.preventDefault();
        items[activeIndex].onClick();
        setIsOpen(false);
      } else if (!isOpen) {
        e.preventDefault();
        setIsOpen(true);
      }
    }
  };

  return (
    <div className="relative inline-block" ref={menuRef} onKeyDown={handleKeyDown}>
      <div
        role="button"
        tabIndex={0}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
      >
        {trigger}
      </div>
      {isOpen && (
        <div
          role="menu"
          className="absolute right-0 top-full mt-2 w-48 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl py-1 z-[60] focus:outline-none"
        >
          {items.map((item, idx) => {
            const isHighlight = idx === activeIndex;
            return (
              <React.Fragment key={idx}>
                {item.isSeparator && <div className="border-t border-slate-800 my-1" />}
                <button
                  role="menuitem"
                  onClick={() => {
                    item.onClick();
                    setIsOpen(false);
                  }}
                  className={`w-full px-4 py-2 text-left text-sm flex items-center gap-2 transition-colors ${isHighlight ? "bg-slate-800" : ""
                    } ${item.danger
                      ? "text-rose-400 hover:text-rose-300 hover:bg-rose-950/30"
                      : "text-slate-200 hover:text-white hover:bg-slate-800"
                    }`}
                >
                  {item.icon}
                  {item.label}
                </button>
              </React.Fragment>
            );
          })}
        </div>
      )}
    </div>
  );
};
