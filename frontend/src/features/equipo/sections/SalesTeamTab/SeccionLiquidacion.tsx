import type { useSalesTeamTab } from "../../hooks/useSalesTeamTab";
import { CommissionDetailModal } from "../../components/CommissionDetailModal";

export function SeccionLiquidacion({ settlement, setCommissionModal }: { settlement: NonNullable<NonNullable<ReturnType<typeof useSalesTeamTab>["commissionModal"]>["settlement"]>; setCommissionModal: ReturnType<typeof useSalesTeamTab>["setCommissionModal"] }) {
  return <CommissionDetailModal identifier={String(settlement.settlement_id)} onClose={() => setCommissionModal(null)} />;
}
