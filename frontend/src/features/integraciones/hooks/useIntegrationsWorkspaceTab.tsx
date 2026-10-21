import * as transporte from "../api/IntegrationsWorkspaceTab";
import { type FormEvent, useEffect, useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";

import { IntegrationConnector } from "../types/IntegrationsWorkspaceTab";
import { IntegrationsWorkspaceTabProps } from "../types/IntegrationsWorkspaceTab";

export function useIntegrationsWorkspaceTab(_props: IntegrationsWorkspaceTabProps) {
  const [connectors, setConnectors] = useState<IntegrationConnector[]>([]);

  const [loading, setLoading] = useState(true);

  const [loadError, setLoadError] = useState<string | null>(null);

  const [testingId, setTestingId] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);

  const [provider, setProvider] = useState("");

  const [category, setCategory] = useState("payments");

  const [mode, setMode] = useState<"test" | "live">("test");

  const [credential, setCredential] = useState("");

  const [editingCredentialId, setEditingCredentialId] = useState<string | null>(null);

  const [saving, setSaving] = useState(false);

  const [revision, setRevision] = useState(0);

  const toast = useToast();

  useEffect(() => {
    let active = true;
    setLoading(true);
    transporte.solicitarDatos()
      .then((response) => {
        if (active && response.items) {
          setConnectors(response.items);
          setLoadError(null);
        }
      })
      .catch((failure: unknown) => {
        if (active) setLoadError(String((failure as { detail?: string }).detail || failure));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [revision]);

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await transporte.solicitarHandleCreate({ provider, category, mode, credential });
      setProvider("");
      setCredential("");
      setShowCreate(false);
      setRevision((value) => value + 1);
      toast.success("Integración configurada", "La credencial se almacenó cifrada y el conector quedó disponible.");
    } catch (failure: unknown) {
      toast.error("No se pudo configurar la integración", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };

  const handleRotateCredential = async (event: FormEvent, connectorId: string) => {
    event.preventDefault();
    setSaving(true);
    try {
      await transporte.solicitarHandleRotateCredential({ connectorId, credential });
      setCredential("");
      setEditingCredentialId(null);
      setRevision((value) => value + 1);
      toast.success("Credencial rotada", "La credencial anterior permanecerá válida durante la ventana de transición.");
    } catch (failure: unknown) {
      toast.error("No se pudo rotar la credencial", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };

  const handleToggleMode = async (connector: IntegrationConnector) => {
    const mode = connector.mode === "live" ? "test" : "live";
    try {
      await transporte.solicitarHandleToggleMode({ connector, mode });
      setConnectors((prev) => prev.map((item) => item.id === connector.id ? { ...item, mode } : item));
      toast.info("Modo actualizado", mode === "live" ? "La integración quedó en modo producción." : "La integración quedó en modo de prueba.");
    } catch (failure: unknown) {
      toast.error("No se pudo actualizar el modo", String((failure as { detail?: string }).detail || failure));
    }
  };

  const handleTestConnection = async (connector: IntegrationConnector) => {
    setTestingId(connector.id);
    try {
      const result = await transporte.solicitarHandleTestConnection({ connector });
      setConnectors((current) => current.map((item) => item.id === connector.id ? { ...item, status: result.status, latency_ms: result.latency_ms, last_sync: result.checked_at, error_message: null } : item));
      toast.success("Configuración verificada", `La presencia y el cifrado de la credencial de ${connector.provider_name} se validaron en ${result.latency_ms} ms.`);
    } catch (failure: unknown) {
      const detail = String((failure as { detail?: string }).detail || failure);
      setConnectors((current) => current.map((item) => item.id === connector.id ? { ...item, status: "error", error_message: detail } : item));
      toast.error("Diagnóstico fallido", detail);
    } finally {
      setTestingId(null);
    }
  };
  return { connectors, loading, loadError, testingId, showCreate, setShowCreate, provider, setProvider, category, setCategory, mode, setMode, credential, setCredential, editingCredentialId, setEditingCredentialId, saving, handleCreate, handleRotateCredential, handleToggleMode, handleTestConnection };
}
