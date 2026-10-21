import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { MotionConfig } from "motion/react";
import { createSalesIAQueryClient } from "./api/remoteState";
import { OperationsWorkspace } from "./app/OperationsWorkspace";
import { SessionGate } from "./app/SessionGate";
import { ToastProvider } from "./ui/toast/ToastContext";
import { QuotationPortal } from "./app/QuotationPortal";
import "./ui/preferences";
import "./index.css";

const queryClient = createSalesIAQueryClient();
const quotationId = new URLSearchParams(window.location.search).get("quotation");

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MotionConfig reducedMotion="never">
        <ToastProvider>
          {quotationId ? <QuotationPortal quotationId={quotationId} /> : <SessionGate><OperationsWorkspace /></SessionGate>}
        </ToastProvider>
      </MotionConfig>
    </QueryClientProvider>
  </React.StrictMode>
);