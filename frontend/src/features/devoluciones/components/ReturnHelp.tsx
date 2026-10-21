import { InfoTooltip } from "../../../ui/components/InfoTooltip";

export function ReturnHelp({ title, description }: { title: string; description: string }) {
  return <InfoTooltip title={title} description={description} interactive className="return-help" />;
}
