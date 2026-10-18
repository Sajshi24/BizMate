import { useQuery } from "@tanstack/react-query";
import { getSales } from "@/services/api";
import { useAuth } from "@/lib/auth-context";

export function useSales(limit?: number) {
  const { user } = useAuth();
  const userId = user?.id ?? "anonymous";

  return useQuery({
    queryKey: ["sales", userId, limit ?? "all"] as const,
    queryFn: () => getSales(limit),
    staleTime: 30_000,
  });
}
