import React, { useState } from "react";
import { Trash2Icon } from "../../icons/index";
import { Modal } from "./Modal";
import { Button } from "./Button";
import { Input } from "./Input";

export interface DestructiveConfirmDialogProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  type: "draft_deletion" | "sale_cancellation";
  entityId?: string;
  id?: string;
}

export const DestructiveConfirmDialog: React.FC<DestructiveConfirmDialogProps> = ({
  isOpen,
  onConfirm,
  onCancel,
  type,
  entityId,
  id
}) => {
  const [confirmationInput, setConfirmationInput] = useState("");

  const isSale = type === "sale_cancellation";
  const title = isSale ? "Anular venta confirmada" : "Eliminar borrador de venta";
  const message = isSale
    ? `Esta acción anula permanentemente el comprobante ${entityId || ""}, emite nota de crédito y revierte el stock del kardex. Acción irreversible con efectos fiscales.`
    : `El borrador ${entityId || ""} no tiene validez fiscal ni reserva inventario. Se eliminará de la base de datos de manera definitiva.`;
  const confirmText = isSale ? "ANULAR" : "";
  const isButtonEnabled = !isSale || confirmationInput === confirmText;

  return (
    <Modal
      id={id}
      isOpen={isOpen}
      onClose={onCancel}
      title={title}
      size="sm"
      footer={
        <div className="flex justify-between w-full">
          <Button variant="ghost" onClick={onCancel}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            disabled={!isButtonEnabled}
            leftIcon={isSale ? undefined : <Trash2Icon size={16} />}
            onClick={onConfirm}
          >
            {isSale ? "Confirmar anulación irreversible" : "Eliminar borrador"}
          </Button>
        </div>
      }
    >
      <div className="space-y-3">
        <p className="text-slate-300 text-sm">{message}</p>
        {isSale && (
          <div>
            <label className="text-xs text-slate-400 block mb-1">
              Escriba &ldquo;ANULAR&rdquo; para autorizar:
            </label>
            <Input
              value={confirmationInput}
              onChange={(e) => setConfirmationInput(e.target.value)}
              placeholder="ANULAR"
            />
          </div>
        )}
      </div>
    </Modal>
  );
};
