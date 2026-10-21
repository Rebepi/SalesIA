import { useCallback, useRef, useState } from "react";
import { ModalSurface } from "./ModalSurface";
import { AlertTriangle } from "lucide-react";

interface ConfirmOptions {
  title: string;
  text: string;
  danger?: boolean;
  confirmLabel?: string;
  cancelLabel?: string;
}

interface PromptOptions {
  title: string;
  label?: string;
  defaultValue?: string;
  placeholder?: string;
}

export function useConfirm() {
  const [state, setState] = useState<(ConfirmOptions & { resolve: (v: boolean) => void }) | null>(null);

  const confirm = useCallback((opts: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setState({ ...opts, resolve });
    });
  }, []);

  const handleClose = (result: boolean) => {
    state?.resolve(result);
    setState(null);
  };

  const ConfirmDialogNode = state ? (
    <ModalSurface labelledBy="confirm-dialog-title" onClose={() => handleClose(false)}>
      <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-700/60 p-6 shadow-2xl shadow-black/40 text-slate-100">
        <div className="flex items-start gap-3">
          {state.danger && (
            <div className="shrink-0 mt-0.5 flex h-9 w-9 items-center justify-center rounded-full bg-rose-500/15">
              <AlertTriangle className="h-5 w-5 text-rose-400" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h2 id="confirm-dialog-title" className="text-base font-bold text-slate-100">
              {state.title}
            </h2>
            <p className="mt-1.5 text-sm text-slate-400 leading-relaxed">{state.text}</p>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={() => handleClose(false)}
            className="rounded-xl border border-slate-600/70 bg-slate-700/80 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-600/80 transition active:scale-95"
          >
            {state.cancelLabel ?? "Cancelar"}
          </button>
          <button
            autoFocus
            onClick={() => handleClose(true)}
            className={`rounded-xl px-4 py-2 text-sm font-semibold text-white shadow-md transition active:scale-95 ${state.danger
                ? "bg-rose-600 hover:bg-rose-500 shadow-rose-900/30"
                : "bg-teal-600 hover:bg-teal-500 shadow-teal-900/30"
              }`}
          >
            {state.confirmLabel ?? "Confirmar"}
          </button>
        </div>
      </div>
    </ModalSurface>
  ) : null;

  return { confirm, ConfirmDialogNode };
}

export function usePrompt() {
  const [state, setState] = useState<(PromptOptions & { resolve: (v: string | null) => void }) | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const prompt = useCallback((opts: PromptOptions): Promise<string | null> => {
    return new Promise((resolve) => {
      setState({ ...opts, resolve });
    });
  }, []);

  const handleClose = (result: string | null) => {
    state?.resolve(result);
    setState(null);
  };

  const PromptDialogNode = state ? (
    <ModalSurface labelledBy="prompt-dialog-title" onClose={() => handleClose(null)}>
      <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-700/60 p-6 shadow-2xl shadow-black/40 text-slate-100">
        <h2 id="prompt-dialog-title" className="text-base font-bold text-slate-100">{state.title}</h2>

        <div className="mt-4">
          {state.label && (
            <label htmlFor="prompt-input" className="block text-sm font-medium text-slate-300 mb-1.5">
              {state.label}
            </label>
          )}
          <input
            id="prompt-input"
            ref={inputRef}
            autoFocus
            type="text"
            defaultValue={state.defaultValue ?? ""}
            placeholder={state.placeholder ?? ""}
            className="w-full rounded-xl border border-slate-600 bg-slate-800 px-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/30"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleClose(inputRef.current?.value ?? "");
              if (e.key === "Escape") handleClose(null);
            }}
          />
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={() => handleClose(null)}
            className="rounded-xl border border-slate-600/70 bg-slate-700/80 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-600/80 transition active:scale-95"
          >
            Cancelar
          </button>
          <button
            onClick={() => handleClose(inputRef.current?.value ?? "")}
            className="rounded-xl bg-teal-600 hover:bg-teal-500 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-teal-900/30 transition active:scale-95"
          >
            Aceptar
          </button>
        </div>
      </div>
    </ModalSurface>
  ) : null;

  return { prompt, PromptDialogNode };
}