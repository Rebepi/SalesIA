import { SeccionNuevaVentaPuntoDeVenta } from "../sections/NewSalePOSModal/SeccionNuevaVentaPuntoDeVenta";
import { useNewSalePOSModal } from "../hooks/useNewSalePOSModal";
import { NewSalePOSModalProps } from "../types/NewSalePOSModal";
import { PosHoldLabelDialog } from "./PosHoldLabelDialog";

export function NewSalePOSModal(props: NewSalePOSModalProps) {
  const hookResult = useNewSalePOSModal(props);
  if (!props.isOpen) return null;

  const {
    holdLabelDialogOpen,
    setHoldLabelDialogOpen,
    holdLabelDefault,
    confirmSuspend,
    ConfirmDialogNode,
    setWarehouses,
    branches,
    roundingMode,
    selectedBranch,
    customerDrawerOpen,
    setCustomerDrawerOpen,
    ...sectionProps
  } = hookResult;

  return (
    <>
      <SeccionNuevaVentaPuntoDeVenta {...sectionProps} />
      {ConfirmDialogNode}
      <PosHoldLabelDialog
        isOpen={holdLabelDialogOpen}
        defaultLabel={holdLabelDefault}
        onConfirm={confirmSuspend}
        onCancel={() => setHoldLabelDialogOpen(false)}
      />
    </>
  );
}
