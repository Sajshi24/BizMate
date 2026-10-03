import type { AuthResponse, LoginCredentials, Product, RegisterData, User } from "@/types";
import { sampleProducts } from "@/services/sample-data";

export const API_URL =
  (import.meta.env["VITE_API_URL"] as string | undefined) ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "bizmate_auth_token";
const USER_KEY = "bizmate_auth_user";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function setStoredUser(user: User): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearStoredAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
  });

  if (!res.ok) {
    let detailMsg = `Request failed (${res.status})`;
    try {
      const errorJson = await res.json();
      if (errorJson && typeof errorJson.detail === "string") {
        detailMsg = errorJson.detail;
      }
    } catch {
      // Use fallback
    }
    throw new Error(detailMsg);
  }

  return (await res.json()) as T;
}

function withTimeout<T>(p: Promise<T>, ms = 3500): Promise<T> {
  return Promise.race([
    p,
    new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}

export async function loginApi(credentials: LoginCredentials): Promise<AuthResponse> {
  try {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg =
        data.detail || (res.status === 401 ? "Invalid email or password." : "Login failed.");
      throw new Error(msg);
    }
    return data as AuthResponse;
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message === "Failed to fetch" || err.message.includes("NetworkError")) {
        throw new Error(
          "Unable to connect to the backend server. Please verify it is running on " + API_URL,
        );
      }
      throw err;
    }
    throw new Error("An unexpected error occurred during login.");
  }
}

export async function registerApi(payload: RegisterData): Promise<AuthResponse> {
  try {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg =
        data.detail ||
        (res.status === 400
          ? "An account with this email already exists."
          : "Registration failed. Please check your details.");
      throw new Error(msg);
    }
    return data as AuthResponse;
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message === "Failed to fetch" || err.message.includes("NetworkError")) {
        throw new Error(
          "Unable to connect to the backend server. Please verify it is running on " + API_URL,
        );
      }
      throw err;
    }
    throw new Error("An unexpected error occurred during registration.");
  }
}

export async function getCurrentUserApi(token: string): Promise<User> {
  const res = await fetch(`${API_URL}/auth/me`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || "Invalid or expired session.");
  }
  return data as User;
}

export async function logoutApi(): Promise<void> {
  try {
    const token = getStoredToken();
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  } catch {
    // Best-effort logout
  }
}

export interface ProductsResult {
  products: Product[];
  source: "live" | "demo";
}

/**
 * Fetches products from the backend API for the authenticated user.
 * Falls back to demo/sample data only if the backend is unreachable (network error).
 * Auth errors (401) propagate rather than silently showing demo data.
 */
export async function getProducts(): Promise<ProductsResult> {
  const token = getStoredToken();
  if (!token) {
    // No token: show empty list (not demo data) so we don't leak data
    return { products: [], source: "live" };
  }

  try {
    const data = await withTimeout(
      (async () => {
        const res = await fetch(`${API_URL}/products`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });
        if (!res.ok) {
          const errorJson = await res.json().catch(() => ({}));
          throw new Error(errorJson.detail || `Request failed (${res.status})`);
        }
        return res.json();
      })(),
    );
    const products = Array.isArray(data) ? data : ((data as { products?: Product[] }).products ?? []);
    return { products, source: "live" };
  } catch (err) {
    const message = err instanceof Error ? err.message : "";
    // Only fall back to demo data for genuine network errors, not auth failures
    if (
      message === "Failed to fetch" ||
      message.includes("NetworkError") ||
      message === "timeout"
    ) {
      return { products: sampleProducts, source: "demo" };
    }
    // Re-throw auth/server errors so the caller can handle them
    throw err;
  }
}

export interface CsvImportResult {
  imported: number;
  message: string;
}

/**
 * Upload a CSV file of products to the backend.
 * The backend derives the user from the JWT token — the frontend does NOT pass a user_id.
 */
export async function importProductsCsv(file: File): Promise<CsvImportResult> {
  const token = getStoredToken();
  if (!token) {
    throw new Error("You must be logged in to import products.");
  }

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/products/import-csv`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      // Do NOT set Content-Type manually — browser sets it with boundary for multipart
    },
    body: formData,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((data as { detail?: string }).detail || `Import failed (${res.status})`);
  }
  return data as CsvImportResult;
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
  login: loginApi,
  register: registerApi,
  getCurrentUser: getCurrentUserApi,
  logout: logoutApi,
  importProductsCsv,
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
