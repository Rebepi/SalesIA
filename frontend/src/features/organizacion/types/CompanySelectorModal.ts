export interface CompanyMembership {
  company_id: string;
  legal_name: string;
  trade_name?: string;
  tax_id: string;
  role: string;
  is_active: boolean;
  is_current?: boolean;
}

export interface CompanySelectorModalProps {
  isOpen: boolean;
  currentCompanyId?: string;
  onClose: () => void;
  onCompanySelected: (company: CompanyMembership) => void;
}
