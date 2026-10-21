import { useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";
import { exportarClientes } from "../api/listadoApi";
import { message } from "../utils/mensajes";

export function useExportarClientes() {
  const [exportingCustomers, setExportingCustomers] = useState(false);
  const toast = useToast();

  async function exportar() {
    setExportingCustomers(true);
    try {
      const res = await exportarClientes();
      const content = typeof res.data === "string" ? res.data : JSON.stringify(res.data, null, 2);
      const blob = new Blob([content], { type: res.format === "csv" ? "text/csv;charset=utf-8" : "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `clientes-${new Date().toISOString().slice(0, 10)}.${res.format}`;
      anchor.click();
      URL.revokeObjectURL(url);
      toast.success("Exportación completada", `${res.count} clientes descargados.`);
    } catch (err) {
      toast.error("Error al exportar", message(err));
    } finally {
      setExportingCustomers(false);
    }
  }

  return { exportingCustomers, exportar };
}
