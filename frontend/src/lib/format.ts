import type { Product, StockStatus } from "@/types";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export const formatMoney = (n: number) => currency.format(n);
export const formatCompact = (n: number) =>
  new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 }).format(n);

export function stockStatus(p: Product): StockStatus {
  if (p.stock <= Math.max(1, Math.floor(p.minimum_stock * 0.35))) return "critical";
  if (p.stock <= p.minimum_stock) return "low";
  return "healthy";
}

export const statusLabel: Record<StockStatus, string> = {
  healthy: "Healthy",
  low: "Low stock",
  critical: "Critical",
};
