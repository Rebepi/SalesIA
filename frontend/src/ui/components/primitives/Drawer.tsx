import React, { useRef, useEffect, useId } from "react";
import { CancelXIcon } from "../../icons/index";
import { IconButton } from "./IconButton";

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  position?: "left" | "right";
  id?: string;
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  children,
  position = "right",
  id
}) => {
  const generatedId = useId();
  const drawerId = id || `drawer-${generatedId.replace(/:/g, "")}`;
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const previousFocused = document.activeElement as HTMLElement | null;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key === "Tab" && drawerRef.current) {
        const focusable = drawerRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    if (drawerRef.current) {
      drawerRef.current.focus();
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previousFocused?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;
  const isLeft = position === "left";

  return (
    <div
      className={`fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex ${isLeft ? "justify-start" : "justify-end"
        }`}
    >
      <div
        ref={drawerRef}
        role="dialog"
        tabIndex={-1}
        aria-modal="true"
        aria-labelledby={`${drawerId}-title`}
        className={`w-full max-w-full sm:max-w-lg md:max-w-xl sm:w-[540px] h-full bg-slate-900 ${isLeft ? "border-r" : "border-l"
          } border-slate-800 shadow-2xl flex flex-col transition-transform duration-300 ease-out focus:outline-none`}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <h3 id={`${drawerId}-title`} className="text-base font-bold text-white">
            {title}
          </h3>
          <IconButton
            ariaLabel="Cerrar panel lateral"
            icon={<CancelXIcon size={18} />}
            onClick={onClose}
          />
        </div>
        <div className="p-5 flex-1 overflow-y-auto text-sm text-slate-200">{children}</div>
      </div>
    </div>
  );
};
