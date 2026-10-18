import { useQuery } from "@tanstack/react-query";
import {
  getAnalyticsSummary,
  getAnalyticsTrend,
  getTopProducts,
  getCategoryPerformance,
} from "@/services/api";
import { useAuth } from "@/lib/auth-context";

export function useAnalyticsSummary() {
  const { user } = useAuth();
  const userId = user?.id ?? "anonymous";

  return useQuery({
    queryKey: ["analytics", "summary", userId] as const,
    queryFn: getAnalyticsSummary,
    staleTime: 30_000,
  });
}

export function useAnalyticsTrend(range: string = "7d") {
  const { user } = useAuth();
  const userId = user?.id ?? "anonymous";

  return useQuery({
    queryKey: ["analytics", "trend", userId, range] as const,
    queryFn: () => getAnalyticsTrend(range),
    staleTime: 30_000,
  });
}

export function useTopProducts() {
  const { user } = useAuth();
  const userId = user?.id ?? "anonymous";

  return useQuery({
    queryKey: ["analytics", "topProducts", userId] as const,
    queryFn: getTopProducts,
    staleTime: 30_000,
  });
}

export function useCategoryPerformance() {
  const { user } = useAuth();
  const userId = user?.id ?? "anonymous";

  return useQuery({
    queryKey: ["analytics", "categoryPerformance", userId] as const,
    queryFn: getCategoryPerformance,
    staleTime: 30_000,
  });
}
