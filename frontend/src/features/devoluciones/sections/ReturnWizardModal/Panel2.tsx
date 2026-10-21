import { ReturnQuantityInput } from "../../components/ReturnQuantityInput";
import { ReturnHelp } from "../../components/ReturnHelp";
import { allowsFractionalReturn } from "../../api/returnFlow";
import type { useReturnWizardModal } from "../../hooks/useReturnWizardModal";


export function Panel2({ lines, quantities, handleQuantityChange, reason, setReason, authorizedException, setAuthorizedException, exceptionReason, setExceptionReason, canAuthorizeException, currency }: { lines: ReturnType<typeof useReturnWizardModal>["lines"]; quantities: ReturnType<typeof useReturnWizardModal>["quantities"]; reason: ReturnType<typeof useReturnWizardModal>["reason"]; setReason: ReturnType<typeof useReturnWizardModal>["setReason"]; authorizedException: ReturnType<typeof useReturnWizardModal>["authorizedException"]; setAuthorizedException: ReturnType<typeof useReturnWizardModal>["setAuthorizedException"]; exceptionReason: ReturnType<typeof useReturnWizardModal>["exceptionReason"]; setExceptionReason: ReturnType<typeof useReturnWizardModal>["setExceptionReason"] } & { canAuthorizeException: boolean; currency: string; handleQuantityChange: (productId: string, val: number, max: number) => void }) {
  return (<div className="space-y-5">
    <div className="return-instructions">
      Selecciona los productos y las cantidades que el cliente desea retornar. No se admiten cantidades
      superiores al total vendido menos retornos previos.
    </div>

    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-[800px] w-full text-left text-xs">
        <thead className="bg-slate-50 text-slate-500">
          <tr>
            <th className="px-4 py-3">Producto / SKU</th>
            <th className="px-3 py-3 text-right">Precio neto unitario <ReturnHelp title="Precio neto unitario" description="Precio después de descuentos de la venta original y antes de impuestos. El cálculo de la devolución incorpora los impuestos y las retenciones aplicables." /></th>
            <th className="px-3 py-3 text-right">Vendido</th>
            <th className="px-3 py-3 text-right">Devuelto / reservado <ReturnHelp title="Devuelto o reservado" description="Suma las unidades de devoluciones aceptadas y de solicitudes pendientes. Las pendientes reservan esas cantidades para evitar devolverlas dos veces." /></th>
            <th className="px-3 py-3 text-right">Disponible <ReturnHelp title="Cantidad disponible" description="Máximo que puedes devolver de esta línea, descontando lo devuelto o reservado y considerando las unidades entregadas." /></th>
            <th className="px-3 py-3 text-center">Cant. Devolver <ReturnHelp title="Cantidad a devolver" description="Selecciona cero para excluir el artículo. Coloca el cursor sobre el campo y gira la rueda del mouse para sumar o restar una unidad; también puedes usar las flechas del teclado. En productos por unidad solo se admiten enteros y nunca se supera la cantidad disponible. Las fracciones se permiten únicamente cuando la unidad del producto las admite." /></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {lines.map((line) => {
            const maxQty = Number(line.eligible_quantity) || 0;
            const currentQty = quantities[line.sale_line_id || line.product_id] || 0;
            return (
              <tr key={line.sale_line_id} className="hover:bg-slate-50/50">
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-900">{line.product_name}</div>
                  <div className="font-mono text-slate-400 text-[11px]">{line.sku}</div>
                </td>
                <td className="px-3 py-3 text-right tabular-nums text-slate-700">
                  {currency} {Number(line.unit_price).toFixed(2)}
                </td>
                <td className="px-3 py-3 text-right tabular-nums">{Number(line.original_quantity).toLocaleString("es-PE", { maximumFractionDigits: 6 })}</td>
                <td className="px-3 py-3 text-right tabular-nums">{Number(line.returned_quantity).toLocaleString("es-PE", { maximumFractionDigits: 6 })}</td>
                <td className="px-3 py-3 text-right tabular-nums">
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-700">
                    {maxQty}
                  </span>
                </td>
                <td className="px-3 py-3 text-center">
                  <ReturnQuantityInput value={currentQty} max={maxQty} allowFractions={allowsFractionalReturn(line)} label={`Cantidad a devolver de ${line.product_name}`} onChange={quantity => handleQuantityChange(line.sale_line_id || line.product_id, quantity, maxQty)} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>

    <div className="space-y-2">
      <div className="return-field-heading"><label htmlFor="return-reason" className="text-xs font-medium text-slate-700">Motivo de devolución <span className="text-red-500">*</span></label><ReturnHelp title="Motivo de devolución" description="Explica por qué se devuelven los productos. Se guarda en la solicitud y permite a la persona revisora entender la operación. Es obligatorio y admite de 3 a 255 caracteres." /></div>
      <input
        id="return-reason"
        type="text"
        minLength={3}
        maxLength={255}
        required
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        placeholder="Indica el motivo comercial o técnico del retorno"
        className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
      />
    </div>

    <div className="return-exception-card">
      <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
        <input
          type="checkbox"
          disabled={!canAuthorizeException}
          checked={authorizedException}
          onChange={(e) => setAuthorizedException(e.target.checked)}
          className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
        />
        <span>Autorizar excepción de plazo comercial o condición</span>
      </label>
      <div className="mt-2"><ReturnHelp title="Excepción autorizada" description="Permite apartarse de determinadas condiciones de la política solo si esta lo admite y la persona tiene autorización. Debe justificarse y no elimina la evidencia obligatoria ni la revisión independiente." /></div>
      {authorizedException && (
        <div className="mt-3">
          <input
            type="text"
            value={exceptionReason}
            onChange={(e) => setExceptionReason(e.target.value)}
            placeholder="Justificación de la excepción aprobada por jefatura"
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-teal-600"
          />
        </div>
      )}
    </div>
  </div>);
}
