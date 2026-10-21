import { useState } from "react";

const denominations: Record<string, number[]> = { PEN: [200, 100, 50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1], USD: [100, 50, 20, 10, 5, 2, 1, 0.25, 0.1, 0.05, 0.01], EUR: [500, 200, 100, 50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01] };

function units(value: string) {
  const [whole, fraction = ""] = value.split(".");
  return BigInt(whole || "0") * 1000000n + BigInt(fraction.padEnd(6, "0"));
}

function decimal(value: bigint) {
  return `${value / 1000000n}.${(value % 1000000n).toString().padStart(6, "0")}`;
}

export function CashDenominationCounter({ currency }: { currency: string }) {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [nonCash, setNonCash] = useState<Record<string, string>>({});
  const [extra, setExtra] = useState<string[]>([]);
  const [newValue, setNewValue] = useState("");
  const [error, setError] = useState("");
  const values = [...(denominations[currency] || []).map(String), ...extra];
  const total = values.reduce((sum, value) => sum + units(value) * BigInt(counts[value] || 0), 0n);
  const format = (value: string) => `${value} ${currency}`;
  function addDenomination() {
    const value = newValue.trim();
    if (!/^\d{1,12}(?:\.\d{1,6})?$/.test(value) || units(value) <= 0n) {
      setError("Ingrese una denominación positiva con hasta seis decimales.");
      return;
    }
    const normalized = decimal(units(value)).replace(/0+$/, "").replace(/\.$/, "");
    if (values.some(existing => units(existing) === units(normalized)) || values.length >= 50) {
      setError("La denominación ya existe o se alcanzó el límite de 50 valores.");
      return;
    }
    setExtra(previous => [...previous, normalized]);
    setNewValue("");
    setError("");
  }
  return <section className="space-y-3">
    <h4 className="text-xs font-bold">Billetes y monedas ({currency})</h4>
    <div className="grid max-h-64 grid-cols-2 gap-2 overflow-y-auto">{values.map(value => <label key={value} className="flex items-center justify-between gap-2 rounded-xl border p-2 text-xs"><span>{format(value)}</span><input aria-label={`Cantidad de ${format(value)}`} type="number" min="0" max="1000000" step="1" value={counts[value] || 0} onChange={event => setCounts(previous => ({ ...previous, [value]: Math.min(1000000, Math.max(0, Math.floor(Number(event.target.value) || 0))) }))} className="w-20 rounded-lg border p-1.5 text-right" /></label>)}</div>
    <div className="flex gap-2"><input aria-label="Otra denominación" value={newValue} onChange={event => setNewValue(event.target.value)} placeholder="Otra denominación" className="min-w-0 flex-1 rounded-xl border p-2 text-xs" /><button type="button" onClick={addDenomination} className="rounded-xl border px-3 text-xs">Añadir</button></div>
    {error && <p role="alert" className="text-xs text-rose-700">{error}</p>}
    <p className="flex justify-between rounded-xl bg-teal-50 p-3 text-sm font-bold text-teal-900"><span>Total efectivo contado</span><output>{format(decimal(total))}</output></p>
    <input name="counted_cash" type="hidden" value={decimal(total)} /><input name="denominations_json" type="hidden" value={JSON.stringify(counts)} />
    <fieldset className="space-y-2 rounded-xl border p-3"><legend className="px-1 text-xs font-semibold">Medios no monetarios (control separado)</legend>{[["CARD", "Tarjetas"], ["TRANSFER", "Transferencias"]].map(([key, label]) => <label key={key} className="flex items-center justify-between gap-2 text-xs">{label}<input aria-label={`Total de ${label.toLowerCase()}`} type="number" min="0" step="0.000001" value={nonCash[key] || ""} onChange={event => setNonCash(previous => ({ ...previous, [key]: event.target.value }))} className="w-28 rounded-lg border p-1.5" /></label>)}<input name="non_cash_json" type="hidden" value={JSON.stringify(Object.fromEntries(Object.entries(nonCash).filter(([, value]) => value !== "")))} /></fieldset>
    <p className="text-xs text-slate-500">Cada caja conserva su moneda. Los medios no monetarios quedan como evidencia del arqueo y no incrementan el efectivo físico.</p>
  </section>;
}
