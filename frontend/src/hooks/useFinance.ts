import { useQuery } from "@tanstack/react-query";
import { getFinanceSummary, getExpenseBreakdown, getMonthlySummary } from "@/services/api";
import { useAuth } from "@/lib/auth-context";

export function useFinanceSummary() {
  const { user } = useAuth();
  const userId = user?.id ?? "anonymous";

  return useQuery({
    queryKey: ["finance", "summary", userId] as const,
    queryFn: getFinanceSummary,
    staleTime: 30_000,
  });
}

export function useExpenseBreakdown() {
  const { user } = useAuth();
  const userId = user?.id ?? "anonymous";

  return useQuery({
    queryKey: ["finance", "expenseBreakdown", userId] as const,
    queryFn: getExpenseBreakdown,
    staleTime: 30_000,
  });
}

export function useMonthlySummary() {
  const { user } = useAuth();
  const userId = user?.id ?? "anonymous";

  return useQuery({
    queryKey: ["finance", "monthlySummary", userId] as const,
    queryFn: getMonthlySummary,
    staleTime: 30_000,
  });
}
