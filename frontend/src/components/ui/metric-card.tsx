import type { LucideIcon } from "lucide-react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function MetricCard({
  label,
  value,
  change,
  context,
  icon: Icon,
  tone = "neutral",
  loading,
}: {
  label: string;
  value: string;
  change?: number;
  context?: string;
  icon: LucideIcon;
  tone?: "neutral" | "warning" | "critical";
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="panel p-5">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="mt-4 h-7 w-32" />
        <Skeleton className="mt-3 h-3 w-40" />
      </div>
    );
  }

  const up = (change ?? 0) >= 0;
  return (
    <div className="panel group p-5 transition-shadow duration-200 hover:shadow-[var(--shadow-raised)]">
      <div className="flex items-start justify-between gap-3">
        <p className="text-[12px] font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <Icon
          className={cn(
            "size-[18px]",
            tone === "critical"
              ? "text-destructive"
              : tone === "warning"
                ? "text-warning"
                : "text-muted-foreground",
          )}
          strokeWidth={1.8}
        />
      </div>
      <p className="num mt-3 text-[26px] font-semibold leading-none tracking-tight text-foreground">
        {value}
      </p>
      <div className="mt-3 flex items-center gap-2 text-[12px]">
        {change !== undefined && (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 font-medium",
              up ? "text-success" : "text-destructive",
            )}
          >
            {up ? <ArrowUpRight className="size-3.5" /> : <ArrowDownRight className="size-3.5" />}
            {Math.abs(change)}%
          </span>
        )}
        {context && <span className="truncate text-muted-foreground">{context}</span>}
      </div>
    </div>
  );
}
