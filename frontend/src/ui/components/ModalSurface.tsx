import { ReactNode, useEffect, useRef } from "react";

export function ModalSurface({ children, labelledBy, onClose, blocked = false, className = "" }: { children: ReactNode; labelledBy: string; onClose: () => void; blocked?: boolean; className?: string }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const element = dialog.current;
    element?.showModal();
    return () => { element?.close(); if (previous?.isConnected) previous.focus(); };
  }, []);
  return <dialog ref={dialog} aria-labelledby={labelledBy} onCancel={event => { event.preventDefault(); if (!blocked) onClose(); }} className={`modal-surface m-auto max-h-[95dvh] max-w-[95vw] overflow-visible border-0 bg-transparent p-0 backdrop:bg-slate-950/60 ${className}`}>{children}</dialog>;
}
