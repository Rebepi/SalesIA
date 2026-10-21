import React from "react";
import { BulbInsightIcon } from "../../icons/index";
import { Button } from "./Button";

export interface EmptyStateProps {
  type: "no_records" | "filter_no_results" | "no_permission" | "not_processed_yet";
  title: string;
  description: string;
  canCreate?: boolean;
  createLabel?: string;
  onCreate?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  type,
  title,
  description,
  canCreate = false,
  createLabel,
  onCreate
}) => {
  return (
    <div
      role="status"
      className="flex flex-col items-center justify-center p-8 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30"
    >
      <div className="p-3 bg-slate-800/80 rounded-2xl text-blue-400 mb-3">
        <BulbInsightIcon size={24} />
      </div>
      <h3 className="text-base font-bold text-white">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm mt-1">{description}</p>
      {type === "no_records" && canCreate && createLabel && onCreate && (
        <div className="mt-4">
          <Button size="sm" variant="primary" onClick={onCreate}>
            {createLabel}
          </Button>
        </div>
      )}
    </div>
  );
};
