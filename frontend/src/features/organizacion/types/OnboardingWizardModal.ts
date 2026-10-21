export interface OnboardingWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCompleted?: () => void;
}

export interface OnboardingFormState {
  tax_id: string;
  legal_name: string;
  trade_name: string;
  base_currency: string;
  branch_code: string;
  branch_name: string;
  timezone: string;
  warehouse_code: string;
  warehouse_name: string;
  series: string;
}
