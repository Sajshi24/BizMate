import { cn } from "@/lib/utils";
import type { StockStatus } from "@/types";
import { statusLabel } from "@/lib/format";

const styles: Record<StockStatus, string> = {
  healthy: "bg-success/10 text-success ring-success/20",
  low: "bg-warning/12 text-warning ring-warning/25",
  critical: "bg-destructive/10 text-destructive ring-destructive/20",
};

export function StatusBadge({ status }: { status: StockStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ring-1 ring-inset",
        styles[status],
      )}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {statusLabel[status]}
    </span>
  );
}
