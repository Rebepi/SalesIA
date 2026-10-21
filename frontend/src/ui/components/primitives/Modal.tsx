import React, { useRef, useEffect, useId } from "react";
import { CancelXIcon } from "../../icons/index";
import { IconButton } from "./IconButton";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  id?: string;
  saveError?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "md",
  id,
  saveError
}) => {
  const generatedId = useId();
  const modalId = id || `modal-${generatedId.replace(/:/g, "")}`;
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const previousFocused = document.activeElement as HTMLElement | null;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key === "Tab" && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
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
    if (dialogRef.current) {
      dialogRef.current.focus();
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previousFocused?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeStyles = {
    sm: "max-w-md",
    md: "max-w-lg",
    lg: "max-w-2xl",
    xl: "max-w-4xl"
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        ref={dialogRef}
        role="dialog"
        tabIndex={-1}
        aria-modal="true"
        aria-labelledby={`${modalId}-title`}
        className={`w-full ${sizeStyles[size]} bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden focus:outline-none`}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <h3 id={`${modalId}-title`} className="text-lg font-bold text-white tracking-wide">
            {title}
          </h3>
          <IconButton ariaLabel="Cerrar modal" icon={<CancelXIcon size={18} />} onClick={onClose} />
        </div>
        {saveError && (
          <div role="alert" className="mx-6 mt-4 p-3 rounded-xl bg-rose-950/60 border border-rose-500/50 text-xs text-rose-300">
            {saveError}
          </div>
        )}
        <div className="p-6 overflow-y-auto text-slate-200 text-sm">{children}</div>
        {footer && (
          <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/40 flex justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};
