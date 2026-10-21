import { FormEvent, ReactNode, useEffect, useState } from "react";
import { LockKeyhole, LoaderCircle, ShieldCheck, Eye, EyeOff } from "lucide-react";
import { apiClient } from "../api/client";

function errorText(error: unknown): string {
  if (typeof error === "object" && error && "detail" in error && typeof error.detail === "string") return error.detail;
  return "No se pudo completar la solicitud. Comprueba la conexión e inténtalo nuevamente.";
}

export function SessionGate({ children }: { children: ReactNode }) {
  const isSsr = typeof window === "undefined";
  const params = !isSsr ? new URLSearchParams(window.location.search) : new URLSearchParams();
  const resetToken = params.get("token");
  const [mode, setMode] = useState<"login" | "recovery" | "reset">(resetToken ? "reset" : "login");
  const hasToken = !isSsr && typeof sessionStorage !== "undefined" && Boolean(sessionStorage.getItem("salesia_access_token"));
  const [ready, setReady] = useState(true);
  const [authenticated, setAuthenticated] = useState(hasToken);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [code, setCode] = useState("");
  const [mfaRequired, setMfaRequired] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const signedOut = () => setAuthenticated(false);
    window.addEventListener("salesia:signed-out", signedOut);
    return () => window.removeEventListener("salesia:signed-out", signedOut);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    let active = true;
    if (resetToken || typeof sessionStorage === "undefined" || !sessionStorage.getItem("salesia_access_token")) {
      setReady(true);
      setAuthenticated(false);
      return;
    }
    apiClient.getMe()
      .then(() => {
        if (active) {
          setAuthenticated(true);
        }
      })
      .catch((failure: unknown) => {
        if (!active) return;
        const status = (failure as { status?: number })?.status;
        if (status === 401 || status === 403) {
          apiClient.clearTokens();
          setAuthenticated(false);
        }
      })
      .finally(() => {
        if (active) {
          setReady(true);
        }
      });
    return () => {
      active = false;
    };
  }, [resetToken]);

  const checkMfa = async (targetEmail: string) => {
    const clean = targetEmail.trim().toLowerCase();
    if (!clean || !clean.includes("@")) {
      setMfaRequired(false);
      return;
    }
    try {
      const res = await apiClient.request<{ mfa_enabled: boolean }>(`/api/v1/auth/mfa-status?email=${encodeURIComponent(clean)}`);
      setMfaRequired(Boolean(res?.mfa_enabled));
    } catch {
      setMfaRequired(false);
    }
  };

  useEffect(() => {
    if (mode !== "login") {
      setMfaRequired(false);
      return;
    }
    const clean = email.trim().toLowerCase();
    if (!clean || !clean.includes("@")) {
      setMfaRequired(false);
      return;
    }
    const timer = setTimeout(() => {
      void checkMfa(clean);
    }, 250);
    return () => clearTimeout(timer);
  }, [email, mode]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true); setError(""); setNotice("");
    try {
      if (mode === "login") {
        await apiClient.login({ email, password, mfa_code: code || undefined });
        setPassword(""); setCode(""); setAuthenticated(true);
      } else if (mode === "recovery") {
        await apiClient.request("/api/v1/auth/password/reset-request", { method: "POST", body: JSON.stringify({ email }) });
        setNotice("Si la cuenta está registrada, recibirá un enlace de recuperación.");
      } else {
        await apiClient.request("/api/v1/auth/password/reset", { method: "POST", body: JSON.stringify({ reset_token: resetToken, new_password: password }) });
        window.history.replaceState(null, "", window.location.pathname);
        setPassword(""); setMode("login"); setNotice("Contraseña actualizada. Ya puedes iniciar sesión.");
      }
    } catch (failure) {
      if (mode === "login" && !mfaRequired) {
        try {
          const res = await apiClient.request<{ mfa_enabled: boolean }>(`/api/v1/auth/mfa-status?email=${encodeURIComponent(email.trim().toLowerCase())}`);
          if (res?.mfa_enabled) {
            setMfaRequired(true);
            setError("Tu cuenta tiene verificación en dos pasos (MFA) activada. Ingresa tu código para continuar.");
            return;
          }
        } catch {
        }
      }
      setError(errorText(failure));
    } finally {
      setBusy(false);
    }
  }

  if (!ready) return <main className="grid min-h-screen place-items-center bg-slate-950 text-white" role="status"><LoaderCircle className="h-8 w-8 motion-safe:animate-spin" /><span>Verificando sesión…</span></main>;
  if (authenticated) return <>{children}</>;
  return <main className="relative isolate grid min-h-[100dvh] items-center overflow-hidden bg-slate-950 px-5 py-10 text-white sm:px-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(380px,0.85fr)] lg:gap-16 lg:px-20 xl:px-28">
    <img src="/images/salesia-login-hero.png" alt="" aria-hidden="true" className="absolute inset-0 -z-30 h-full w-full object-cover object-[46%_center]" />
    <div aria-hidden="true" className="absolute inset-0 -z-20 bg-[linear-gradient(90deg,rgba(2,6,23,0.34)_0%,rgba(2,6,23,0.38)_42%,rgba(2,6,23,0.78)_72%,rgba(2,6,23,0.9)_100%)]" />
    <div aria-hidden="true" className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_72%_48%,rgba(13,148,136,0.13),transparent_32%)]" />
    <section className="mb-9 max-w-2xl self-end pb-2 drop-shadow-[0_2px_16px_rgba(0,0,0,0.65)] lg:mb-0 lg:self-center lg:pb-0">
      <div className="mb-6 inline-flex items-center gap-3 rounded-full border border-white/20 bg-slate-950/35 px-4 py-2 text-sm font-semibold tracking-wide text-white backdrop-blur-md">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-teal-500/20 ring-1 ring-teal-300/35"><ShieldCheck className="h-5 w-5 text-teal-300" /></span>
        SalesIA Enterprise
      </div>
      <h1 className="max-w-xl text-4xl font-bold leading-[1.08] tracking-tight sm:text-5xl xl:text-6xl">Tu operación comercial, conectada e inteligente.</h1>
      <p className="mt-5 max-w-lg text-base leading-relaxed text-slate-200 sm:text-lg">Gestiona ventas, clientes, inventario, finanzas y analítica desde una plataforma empresarial segura.</p>
      <div className="mt-7 hidden flex-wrap gap-2 text-xs font-medium text-slate-200 sm:flex">
        <span className="rounded-full border border-white/15 bg-slate-950/30 px-3 py-1.5 backdrop-blur-sm">Analítica comercial</span>
        <span className="rounded-full border border-white/15 bg-slate-950/30 px-3 py-1.5 backdrop-blur-sm">Inventario conectado</span>
        <span className="rounded-full border border-white/15 bg-slate-950/30 px-3 py-1.5 backdrop-blur-sm">Seguridad empresarial</span>
      </div>
    </section>
    <section className="mx-auto w-full max-w-[440px] rounded-[28px] border border-white/20 bg-slate-950/55 p-6 text-white shadow-[0_32px_80px_-24px_rgba(0,0,0,0.8)] ring-1 ring-white/5 backdrop-blur-2xl sm:p-8" id="scr-001-login-card">
      <div className="mb-6 flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-2xl border border-teal-300/25 bg-teal-400/15"><LockKeyhole className="h-5 w-5 text-teal-200" /></span><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-300">Acceso seguro</p><h2 className="mt-0.5 text-2xl font-semibold tracking-tight">{mode === "login" ? "Iniciar sesión" : mode === "recovery" ? "Recuperar acceso" : "Establecer contraseña"}</h2></div></div>
      <form onSubmit={submit} className="mt-7 space-y-5" aria-busy={busy}>
        {mode !== "reset" && (
          <label className="block text-sm font-medium text-slate-100" htmlFor="session-email">
            Correo de trabajo
            <input
              id="session-email"
              name="username"
              autoFocus
              type="email"
              autoComplete="username"
              required
              value={email}
              onBlur={() => void checkMfa(email)}
              onChange={event => setEmail(event.target.value)}
              className="mt-2 w-full rounded-xl border border-white/15 bg-slate-950/45 px-4 py-3 text-white shadow-inner outline-none transition placeholder:text-slate-500 hover:border-white/25 focus:border-teal-300 focus:ring-4 focus:ring-teal-400/15"
            />
          </label>
        )}
        {mode !== "recovery" && (
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-100" htmlFor="session-password">Contraseña</label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="flex items-center gap-1 text-xs text-slate-300 hover:text-white focus-visible:outline focus-visible:outline-teal-300"
                aria-label={showPassword ? "Ocultar contraseña" : "Ver contraseña"}
              >
                {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                <span>{showPassword ? "Ocultar" : "Mostrar"}</span>
              </button>
            </div>
            <input
              id="session-password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete={mode === "reset" ? "new-password" : "current-password"}
              minLength={mode === "reset" ? 12 : 1}
              required
              value={password}
              onChange={event => setPassword(event.target.value)}
              className="w-full rounded-xl border border-white/15 bg-slate-950/45 px-4 py-3 text-white shadow-inner outline-none transition placeholder:text-slate-500 hover:border-white/25 focus:border-teal-300 focus:ring-4 focus:ring-teal-400/15"
            />
          </div>
        )}
        {mode === "login" && (
          <div className={mfaRequired ? "space-y-1 block" : "hidden"}>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-100" htmlFor="session-mfa">
                Código MFA o de recuperación
              </label>
              <span className="rounded-full border border-teal-300/25 bg-teal-400/15 px-2 py-0.5 text-[10px] font-bold text-teal-200">
                Requerido
              </span>
            </div>
            <input
              id="session-mfa"
              name="mfa_code"
              aria-label="MFA requerido"
              autoComplete="one-time-code"
              placeholder="123456"
              value={code}
              onChange={event => setCode(event.target.value)}
              className="mt-1 w-full rounded-xl border border-white/15 bg-slate-950/45 px-4 py-3 text-white shadow-inner outline-none transition placeholder:text-slate-500 hover:border-white/25 focus:border-teal-300 focus:ring-4 focus:ring-teal-400/15"
            />
          </div>
        )}
        {error && <p role="alert" className="rounded-xl border border-rose-300/25 bg-rose-950/55 p-4 text-sm text-rose-100">{error}</p>}
        {notice && <p role="status" className="rounded-xl border border-teal-300/25 bg-teal-950/55 p-4 text-sm text-teal-100">{notice}</p>}
        <button disabled={busy} className="flex w-full items-center justify-center gap-2 rounded-xl bg-teal-500 px-5 py-3 font-semibold text-slate-950 shadow-lg shadow-teal-950/30 transition hover:bg-teal-300 focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-teal-200 disabled:cursor-wait disabled:opacity-60 motion-safe:active:scale-[.98]">
          {busy && <LoaderCircle className="h-4 w-4 motion-safe:animate-spin" />}
          {mode === "login" ? "Iniciar Sesión" : mode === "recovery" ? "Solicitar enlace" : "Guardar contraseña"}
        </button>
        {mode !== "reset" && (
          <button type="button" onClick={() => { setMode(mode === "login" ? "recovery" : "login"); setError(""); setNotice(""); }} className="w-full rounded-lg py-2 text-sm font-medium text-teal-200 underline-offset-4 hover:text-teal-100 hover:underline focus-visible:outline focus-visible:outline-teal-300">
            {mode === "login" ? "¿Olvidaste tu contraseña?" : "Volver a iniciar sesión"}
          </button>
        )}
      </form>
    </section>
  </main>;
}
