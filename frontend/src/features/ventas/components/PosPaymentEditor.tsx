import { useEffect, useMemo, useState, useRef } from "react";
import { CreditCard, Plus, Trash2 } from "lucide-react";
import { apiClient } from "../../../api/client";
import { useOperatingProfile } from "../../organizacion/components/OperatingProfileContext";

export interface CheckoutPayment {
  key: string;
  method: string;
  amount: number;
  cashTendered?: number;
  referenceCode?: string;
  cashSessionId?: string;
  isManual?: boolean;
  isManualCash?: boolean;
}

interface PaymentMethod {
  code: string;
  name: string;
  requires_reference: boolean;
  requires_cash_session: boolean;
  allowed_currencies: string[];
  is_active: boolean;
}

interface CashSession {
  session_id: string;
  branch_id: string;
  terminal_code: string;
  status: string;
}

interface Props {
  total: number;
  currency: string;
  branchId?: string;
  disabled?: boolean;
  onChange: (payments: CheckoutPayment[], valid: boolean) => void;
  onCountChange?: (count: number) => void;
}

function amount(value: number) {
  return Number.isFinite(value) ? Math.max(0, value) : 0;
}

function round2(val: number) {
  return Math.round(val * 100) / 100;
}

function rebalance(list: CheckoutPayment[], targetTotal: number): CheckoutPayment[] {
  const manualSum = list.filter(p => p.isManual).reduce((sum, p) => sum + amount(p.amount), 0);
  const autoLines = list.filter(p => !p.isManual);
  if (!autoLines.length) return list;
  const pool = Math.max(0, round2(targetTotal - manualSum));
  const base = Math.floor((pool / autoLines.length) * 100) / 100;
  let allocated = 0;
  return list.map(payment => {
    if (payment.isManual) return payment;
    const isLastAuto = payment.key === autoLines[autoLines.length - 1].key;
    const lineAmt = isLastAuto ? round2(pool - allocated) : base;
    allocated += base;
    const nextCash = payment.method === "CASH" ? (payment.isManualCash ? payment.cashTendered : lineAmt) : undefined;
    return { ...payment, amount: lineAmt, cashTendered: nextCash };
  });
}

export function PosPaymentEditor({ total, currency, branchId, disabled, onChange, onCountChange }: Props) {
  const { enabled } = useOperatingProfile();
  const cashEnabled = enabled("cash");
  const [methods, setMethods] = useState<PaymentMethod[]>([]);
  const [sessions, setSessions] = useState<CashSession[]>([]);
  const [payments, setPayments] = useState<CheckoutPayment[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollDown, setCanScrollDown] = useState(false);

  function checkScroll() {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollDown(el.scrollHeight - el.scrollTop - el.clientHeight > 4);
  }

  useEffect(() => {
    checkScroll();
  }, [payments]);

  useEffect(() => {
    window.addEventListener("resize", checkScroll);
    return () => window.removeEventListener("resize", checkScroll);
  }, []);

  useEffect(() => {
    apiClient.request<PaymentMethod[]>("/api/v1/payment-methods").then(methodRows => {
      setMethods(methodRows.filter(method => method.is_active && method.allowed_currencies.includes(currency) && (cashEnabled || method.code !== "CASH")));
    });
  }, [currency, cashEnabled]);

  useEffect(() => {
    if (!branchId) {
      setSessions([]);
      return;
    }
    apiClient.request<{ session: CashSession | null }>(`/api/v1/cash-sessions/current?branch_id=${branchId}`).then(response => setSessions(response.session ? [response.session] : [])).catch(() => setSessions([]));
  }, [branchId]);

  useEffect(() => {
    setPayments(previous => {
      if (total <= 0 || !methods.length) return previous;
      const first = methods.find(method => method.code === "CASH") || methods[0];
      if (!previous.length) {
        return [{
          key: crypto.randomUUID(),
          method: first.code,
          amount: round2(total),
          cashTendered: first.code === "CASH" ? round2(total) : undefined,
          isManual: false,
          isManualCash: false
        }];
      }
      return rebalance(previous, total);
    });
  }, [total, methods]);

  const activeSession = sessions.find(session => session.branch_id === branchId && session.status === "open");
  const paid = useMemo(() => payments.reduce((sum, payment) => sum + amount(payment.amount), 0), [payments]);
  const change = useMemo(() => payments.reduce((sum, payment) => payment.method === "CASH" ? sum + Math.max(0, amount(payment.cashTendered || 0) - amount(payment.amount)) : sum, 0), [payments]);
  const invalidReference = payments.some(payment => methods.find(method => method.code === payment.method)?.requires_reference && !payment.referenceCode?.trim());
  const invalidCashTendered = payments.some(payment => payment.method === "CASH" && amount(payment.cashTendered || 0) < amount(payment.amount));
  const cashWithoutSession = payments.some(payment => payment.method === "CASH") && !activeSession;
  const pending = Math.max(0, round2(total - paid));
  const valid = payments.length > 0 && payments.every(payment => methods.some(method => method.code === payment.method)) && paid > 0 && pending <= 0.005 && !invalidReference && !invalidCashTendered && !cashWithoutSession;

  const maxPayments = Math.min(4, methods.length > 0 ? methods.length : 4);
  const isMaxReached = payments.length >= maxPayments;

  useEffect(() => {
    onChange(payments.map(payment => ({ ...payment, cashSessionId: payment.method === "CASH" ? activeSession?.session_id : undefined })), valid);
    onCountChange?.(payments.length);
  }, [payments, activeSession?.session_id, valid]);

  function update(key: string, patch: Partial<CheckoutPayment>) {
    setPayments(previous => previous.map(payment => payment.key === key ? { ...payment, ...patch } : payment));
  }

  function handleMethodChange(key: string, nextMethod: string) {
    setPayments(previous => previous.map(payment => {
      if (payment.key !== key) return payment;
      return {
        ...payment,
        method: nextMethod,
        referenceCode: "",
        cashTendered: nextMethod === "CASH" ? payment.amount : undefined,
        isManualCash: false
      };
    }));
  }

  function handleAmountChange(key: string, nextAmt: number) {
    setPayments(previous => previous.map(payment => {
      if (payment.key !== key) return payment;
      const nextCash = payment.method === "CASH" ? (payment.isManualCash ? payment.cashTendered : nextAmt) : undefined;
      return { ...payment, amount: nextAmt, isManual: true, cashTendered: nextCash };
    }));
  }

  function handleCashTenderedChange(key: string, nextCash: number) {
    setPayments(previous => previous.map(payment => {
      if (payment.key !== key) return payment;
      return { ...payment, cashTendered: nextCash, isManualCash: true };
    }));
  }

  function removePayment(key: string) {
    if (payments.length <= 1) return;
    const remaining = payments.filter(p => p.key !== key);
    if (remaining.length === 1) {
      if (!remaining[0].isManual) {
        const full = round2(total);
        const nextCash = remaining[0].method === "CASH" && !remaining[0].isManualCash ? full : remaining[0].cashTendered;
        setPayments([{ ...remaining[0], amount: full, cashTendered: nextCash }]);
        return;
      }
      setPayments(remaining);
      return;
    }
    setPayments(rebalance(remaining, total));
  }

  function addPayment() {
    if (!methods.length || isMaxReached) return;
    const currentPending = Math.max(0, round2(total - paid));
    const defaultMethod = methods.find(m => m.code !== payments[payments.length - 1]?.method) || methods[0];
    if (currentPending > 0.005) {
      const newLine: CheckoutPayment = {
        key: crypto.randomUUID(),
        method: defaultMethod.code,
        amount: currentPending,
        cashTendered: defaultMethod.code === "CASH" ? currentPending : undefined,
        referenceCode: "",
        isManual: false,
        isManualCash: false
      };
      setPayments(previous => [...previous, newLine]);
      return;
    }
    const newLine: CheckoutPayment = {
      key: crypto.randomUUID(),
      method: defaultMethod.code,
      amount: 0,
      referenceCode: "",
      isManual: false,
      isManualCash: false
    };
    const all = [...payments, newLine];
    const autoCount = all.filter(p => !p.isManual).length;
    if (autoCount === 1) {
      const lastIdx = payments.length - 1;
      const prevLast = payments[lastIdx];
      const half = round2(prevLast.amount / 2);
      const other = round2(prevLast.amount - half);
      const updatedPrev = {
        ...prevLast,
        amount: half,
        cashTendered: prevLast.method === "CASH" && !prevLast.isManualCash ? half : prevLast.cashTendered
      };
      newLine.amount = other;
      newLine.cashTendered = newLine.method === "CASH" ? other : undefined;
      setPayments([...payments.slice(0, lastIdx), updatedPrev, newLine]);
      return;
    }
    setPayments(rebalance(all, total));
  }

  return (
    <div className="space-y-1.5 rounded-2xl border border-slate-200 bg-white p-2 dark:border-slate-800 dark:bg-slate-900/90">
      <div className="flex shrink-0 items-center justify-between">
        <div className="flex items-center gap-1.5">
          <CreditCard className="h-3.5 w-3.5 text-teal-700 dark:text-teal-400" />
          <strong className="text-xs text-slate-800 dark:text-slate-100">Medios de pago ({payments.length})</strong>
        </div>
        <button
          type="button"
          disabled={disabled || total <= 0 || isMaxReached}
          onClick={addPayment}
          title={isMaxReached ? `Límite alcanzado (${maxPayments} medios de pago máximo)` : "Dividir pago"}
          className="inline-flex items-center gap-1 text-[10px] font-semibold text-teal-700 dark:text-teal-400 disabled:opacity-40"
        >
          <Plus className="h-3 w-3" />
          <span>Dividir pago</span>
        </button>
      </div>

      <div className="grid gap-x-1.5" style={{ gridTemplateColumns: "minmax(130px,1.6fr) 76px minmax(90px,1fr) 28px" }}>
        <span className="pl-1 text-[8px] font-bold uppercase tracking-wider text-slate-400">Medio</span>
        <span className="pl-1 text-[8px] font-bold uppercase tracking-wider text-slate-400">Importe</span>
        <span className="pl-1 text-[8px] font-bold uppercase tracking-wider text-slate-400">Recibido / Referencia</span>
        <span />
      </div>

      <div className="relative">
        <div
          ref={scrollRef}
          onScroll={checkScroll}
          className="max-h-[220px] [@media(max-height:768px)]:max-h-[160px] overflow-y-auto space-y-0.5 [scrollbar-width:thin] [scrollbar-color:#94a3b8_transparent] dark:[scrollbar-color:#475569_transparent]"
        >
          {payments.map((payment, index) => (
            <div
              key={payment.key}
              className="grid items-center gap-x-1.5 py-1 border-b border-slate-100 dark:border-slate-800 last:border-0"
              style={{ gridTemplateColumns: "minmax(130px,1.6fr) 76px minmax(90px,1fr) 28px" }}
            >
              <select
                aria-label="Medio de pago"
                value={payment.method}
                onChange={event => handleMethodChange(payment.key, event.target.value)}
                className="h-[36px] w-full rounded-lg border border-slate-300 bg-white px-2 text-[11px] font-semibold dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 outline-none focus:border-teal-600 cursor-pointer"
              >
                {methods.map(item => {
                  const label = item.name === "Tarjeta de Débito / Crédito" ? "Tarjeta Débito / Crédito" : item.name;
                  return (
                    <option key={item.code} value={item.code} title={item.name}>
                      {label}
                    </option>
                  );
                })}
              </select>

              <input
                aria-label={`Importe del pago ${index + 1}`}
                type="number"
                min="0.01"
                step="0.01"
                value={payment.amount || ""}
                onChange={event => handleAmountChange(payment.key, amount(Number(event.target.value)))}
                className="h-[36px] w-full rounded-lg border border-slate-300 bg-white px-2 text-[11px] font-mono font-bold dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 outline-none focus:border-teal-600"
              />

              {payment.method === "CASH" ? (
                <input
                  aria-label="Efectivo recibido"
                  type="number"
                  min={payment.amount}
                  step="0.01"
                  value={payment.cashTendered ?? ""}
                  onChange={event => handleCashTenderedChange(payment.key, amount(Number(event.target.value)))}
                  placeholder="Efectivo recibido"
                  title="Efectivo recibido"
                  className="h-[36px] w-full rounded-lg border border-slate-300 bg-white px-2 text-[11px] font-mono font-bold placeholder:text-slate-400 placeholder:font-normal dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 outline-none focus:border-teal-600"
                />
              ) : (
                <input
                  aria-label="Referencia de operación"
                  value={payment.referenceCode || ""}
                  onChange={event => update(payment.key, { referenceCode: event.target.value })}
                  placeholder={
                    methods.find(m => m.code === payment.method)?.requires_reference
                      ? "N° op. (requerido)"
                      : "N° operación"
                  }
                  title="Referencia o código de aprobación del voucher"
                  className={`h-[36px] w-full rounded-lg border bg-white px-2 text-[11px] font-mono placeholder:text-slate-400 placeholder:font-normal dark:bg-slate-900 dark:text-slate-100 outline-none transition ${
                    methods.find(m => m.code === payment.method)?.requires_reference && !payment.referenceCode?.trim()
                      ? "border-amber-400 dark:border-amber-600 focus:border-amber-500"
                      : "border-slate-300 dark:border-slate-700 focus:border-teal-600"
                  }`}
                />
              )}

              <button
                type="button"
                disabled={payments.length === 1}
                onClick={() => removePayment(payment.key)}
                className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:text-slate-500 dark:hover:bg-rose-950/40 dark:hover:text-rose-400 disabled:opacity-20 transition"
                aria-label="Quitar medio de pago"
                title="Quitar medio de pago"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
        {canScrollDown && (
          <div className="pointer-events-none absolute bottom-0 inset-x-0 h-4 bg-gradient-to-t from-white dark:from-slate-900 to-transparent rounded-b-xl" />
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[10px] text-slate-600 dark:text-slate-300 pt-1 border-t border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-1">
          <span>Registrado:</span>
          <strong className="font-mono text-slate-800 dark:text-slate-100">{currency} {paid.toFixed(2)}</strong>
        </div>
        <div className="flex items-center gap-1">
          <span>Pendiente:</span>
          <strong className={`font-mono ${pending > 0.005 ? "text-amber-600 dark:text-amber-400" : "text-slate-800 dark:text-slate-100"}`}>
            {currency} {pending.toFixed(2)}
          </strong>
        </div>
        {change > 0 && (
          <div className="flex items-center gap-1 text-teal-700 dark:text-teal-400 font-semibold">
            <span>Vuelto:</span>
            <strong className="font-mono">{currency} {change.toFixed(2)}</strong>
          </div>
        )}
      </div>

      {cashWithoutSession && (
        <p role="alert" className="truncate rounded-md bg-amber-50 px-2 py-0.5 text-[9px] text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
          No hay turno de caja abierto para esta sede. Abre un turno o usa otro medio.
        </p>
      )}
      {invalidCashTendered && (
        <p role="alert" className="truncate rounded-md bg-rose-50 px-2 py-0.5 text-[9px] text-rose-700 dark:bg-rose-950/40 dark:text-rose-400">
          El efectivo recibido no puede ser menor que el importe en efectivo.
        </p>
      )}
      {invalidReference && (
        <p role="alert" className="truncate rounded-md bg-rose-50 px-2 py-0.5 text-[9px] text-rose-700 dark:bg-rose-950/40 dark:text-rose-400">
          Completa la referencia requerida para tarjeta o transferencia.
        </p>
      )}
    </div>
  );
}

