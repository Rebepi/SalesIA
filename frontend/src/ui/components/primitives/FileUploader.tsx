import React, { useState, useRef } from "react";

export const FileUploader: React.FC<{
  onFileSelect: (file: File) => void;
  acceptedFormats?: string;
}> = ({ onFileSelect, acceptedFormats }) => {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      inputRef.current?.click();
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none ${dragOver
        ? "border-blue-500 bg-blue-950/20"
        : "border-slate-700 hover:border-slate-600 bg-slate-900/40"
        }`}
    >
      <input
        type="file"
        ref={inputRef}
        accept={acceptedFormats}
        className="hidden"
        onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
      />
      <div className="text-slate-400 text-sm pointer-events-none">
        <p className="font-semibold text-slate-200">
          Arrastre un archivo o haga clic para examinar
        </p>
        <p className="text-xs text-slate-500 mt-1">
          Formatos admitidos: {acceptedFormats || "Todos los archivos"}
        </p>
      </div>
    </div>
  );
};
