import { useQuery } from "@tanstack/react-query";
import { getProducts } from "@/services/api";
import { useAuth } from "@/lib/auth-context";

export const productsQueryOptions = {
  queryKey: ["products"] as const,
  queryFn: getProducts,
  staleTime: 30_000,
};

export function useProducts() {
  const { user } = useAuth();
  const userId = user?.id ?? "anonymous";

  return useQuery({
    queryKey: ["products", userId] as const,
    queryFn: getProducts,
    staleTime: 30_000,
  });
}
