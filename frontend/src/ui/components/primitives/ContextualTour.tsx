import React, { useState } from "react";
import { Button } from "./Button";

export interface TourStep {
  title: string;
  description: string;
}

export const ContextualTour: React.FC<{
  tourId: string;
  userId: string;
  steps: TourStep[];
  isOpen: boolean;
  onClose: () => void;
}> = ({ tourId, userId, steps, isOpen, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const storageKey = `tour_dismissed_${tourId}_${userId}`;

  const dismissTour = () => {
    localStorage.setItem(storageKey, "true");
    onClose();
  };

  if (!isOpen) return null;

  const step = steps[currentStep];

  return (
    <div
      role="region"
      aria-label="Guía interactiva"
      className="fixed bottom-6 right-6 z-40 w-80 bg-slate-900 border border-blue-500/60 rounded-2xl shadow-2xl p-4 text-left space-y-2"
    >
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <span className="text-xs font-bold text-white">
          {`${step.title} (${currentStep + 1}/${steps.length})`}
        </span>
        <button
          type="button"
          onClick={dismissTour}
          className="text-slate-400 hover:text-white text-xs"
          aria-label="Omitir tour"
        >
          Omitir
        </button>
      </div>
      <p className="text-xs text-slate-300">{step.description}</p>
      <div className="flex justify-between items-center pt-2">
        <Button
          size="sm"
          variant="ghost"
          disabled={currentStep === 0}
          onClick={() => setCurrentStep((p) => p - 1)}
        >
          Anterior
        </Button>
        {currentStep < steps.length - 1 ? (
          <Button size="sm" variant="primary" onClick={() => setCurrentStep((p) => p + 1)}>
            Siguiente
          </Button>
        ) : (
          <Button size="sm" variant="primary" onClick={dismissTour}>
            Finalizar
          </Button>
        )}
      </div>
    </div>
  );
};
