import React, { useState } from "react";
import { FileUploader } from "./FileUploader";
import { ProgressBar } from "./ProgressBar";
import { Button } from "./Button";

export interface EnterpriseFileStatus {
  file: File;
  progress: number;
  status: "scanning" | "approved" | "rejected";
  publicDownloadUrl?: string;
  rejectionReason?: string;
}

export const EnterpriseFileUploader: React.FC<{
  onFileSelect: (file: File) => void;
  acceptedFormats?: string[];
  maxSizeMb?: number;
  fileStatus?: EnterpriseFileStatus | null;
  onCancel?: () => void;
}> = ({
  onFileSelect,
  acceptedFormats = [".pdf", ".xlsx", ".xml"],
  maxSizeMb = 10,
  fileStatus,
  onCancel
}) => {
    const [error, setError] = useState<string | null>(null);

    const handleFile = (file: File) => {
      setError(null);
      const sizeMb = file.size / (1024 * 1024);
      if (sizeMb > maxSizeMb) {
        setError(`El archivo excede el tamaño máximo permitido de ${maxSizeMb} MB`);
        return;
      }
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      if (!acceptedFormats.includes(ext)) {
        setError(`Formato no admitido. Permitidos: ${acceptedFormats.join(", ")}`);
        return;
      }
      onFileSelect(file);
    };

    return (
      <div className="space-y-3 w-full text-left">
        <FileUploader
          acceptedFormats={acceptedFormats.join(",")}
          onFileSelect={handleFile}
        />
        {error && <span role="alert" className="text-xs text-rose-400">{error}</span>}
        {fileStatus && (
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-xs space-y-2">
            <div className="flex justify-between items-center text-slate-300">
              <span>{fileStatus.file.name}</span>
              <span>{fileStatus.progress}%</span>
            </div>
            <ProgressBar progress={fileStatus.progress} />
            <div className="flex justify-between items-center pt-1">
              <span
                className={`font-semibold ${fileStatus.status === "approved"
                  ? "text-emerald-400"
                  : fileStatus.status === "scanning"
                    ? "text-blue-400"
                    : "text-rose-400"
                  }`}
              >
                {`Estado de seguridad: ${fileStatus.status === "approved" ? "Aprobado" : fileStatus.status === "scanning" ? "Escaneando..." : "Rechazado"}`}
              </span>
              {fileStatus.status === "approved" && fileStatus.publicDownloadUrl ? (
                <a
                  href={fileStatus.publicDownloadUrl}
                  download
                  className="text-blue-400 underline hover:text-blue-300"
                >
                  Descargar archivo
                </a>
              ) : (
                <span className="text-slate-500 cursor-not-allowed">
                  Descarga no permitida (No aprobado)
                </span>
              )}
              {onCancel && fileStatus.status === "scanning" && (
                <Button size="sm" variant="ghost" onClick={onCancel}>
                  Cancelar subida
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };
