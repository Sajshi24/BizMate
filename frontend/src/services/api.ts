import type { Product } from "@/types";
import { sampleProducts } from "@/services/sample-data";

export const API_URL =
  (import.meta.env["VITE_API_URL"] as string | undefined) ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return (await res.json()) as T;
}

function withTimeout<T>(p: Promise<T>, ms = 3500): Promise<T> {
  return Promise.race([
    p,
    new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}

export interface ProductsResult {
  products: Product[];
  source: "live" | "demo";
}

/**
 * Fetches products from the business API. When the API is unreachable
 * (e.g. the local service is not running) we fall back to demo data so the
 * interface stays usable, and flag it so the UI can say so.
 */
export async function getProducts(): Promise<ProductsResult> {
  try {
    const data = await withTimeout(request<Product[] | { products: Product[] }>("/products"));
    const products = Array.isArray(data) ? data : (data.products ?? []);
    return { products, source: "live" };
  } catch {
    return { products: sampleProducts, source: "demo" };
  }
}

export async function getHealth(): Promise<boolean> {
  try {
    await withTimeout(request<unknown>("/health"), 2000);
    return true;
  } catch {
    return false;
  }
}

/** Placeholders for endpoints that are not available on the API yet. */
export const api = {
  getProducts,
  getHealth,
  recordSale: async (_lines: { product_id: string; qty: number }[]) => {
    await new Promise((r) => setTimeout(r, 700));
    return { ok: true as const };
  },
  generateCampaign: async (input: { product: string; type: string; details: string }) => {
    await new Promise((r) => setTimeout(r, 1200));
    return {
      content: `${input.type} — ${input.product}\n\nFresh stock just landed. ${
        input.details || "Quality you can trust, at a price that works for your family."
      }\n\nAvailable now in store. Limited quantities — visit us today.\n\n#SmallBusiness #${input.product.replace(/\s+/g, "")} #ShopLocal`,
    };
  },
  askAdvisor: async (question: string, products: import("@/types").Product[]) => {
    await new Promise((r) => setTimeout(r, 900));
    const low = products.filter((p) => p.stock <= p.minimum_stock);
    const q = question.toLowerCase();
    if (q.includes("restock") || q.includes("attention") || q.includes("stock")) {
      return low.length
        ? `${low.length} product${low.length > 1 ? "s need" : " needs"} restocking soon: ${low
            .slice(0, 4)
            .map((p) => `${p.name} (${p.stock} left)`)
            .join(", ")}. Reordering these first protects your fastest-moving revenue.`
        : "Every product is currently above its minimum stock level. Nothing needs reordering today.";
    }
    if (q.includes("sales") || q.includes("performing")) {
      return "Sales are trending up around 12% versus the previous period, with weekends carrying the strongest volume. Keep your top three sellers well stocked through Friday.";
    }
    return `You are carrying ${products.length} products across ${
      new Set(products.map((p) => p.category)).size
    } categories. Margins look healthiest in your grocery lines, while ${
      low[0]?.name ?? "your top seller"
    } is the item most worth watching this week.`;
  },
};
