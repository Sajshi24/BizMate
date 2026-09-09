import { useQuery } from "@tanstack/react-query";
import { getProducts } from "@/services/api";

export const productsQueryOptions = {
  queryKey: ["products"] as const,
  queryFn: getProducts,
  staleTime: 60_000,
};

export function useProducts() {
  return useQuery(productsQueryOptions);
}
