import { apiClient } from "../../../api/client";
import { OnboardingFormState } from "../types/OnboardingWizardModal";

export function solicitarHandleSubmit({ formData }: { formData: OnboardingFormState }) {
  return apiClient.request<{ status: string; resumed?: boolean }>(
    "/api/v1/organization/onboarding/setup",
    {
      method: "POST",
      body: JSON.stringify(formData)
    }
  );
}
