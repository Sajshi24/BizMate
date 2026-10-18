import type {
  AnalyticsSummary,
  AuthResponse,
  CategoryPerformanceItem,
  ExpenseItem,
  FinanceSummary,
  LoginCredentials,
  MonthlySummaryItem,
  Product,
  RegisterData,
  SaleRecord,
  TopProductItem,
  TrendPoint,
  User,
} from "@/types";

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
    const error = new Error(data.detail || "Invalid or expired session.");
    (error as Error & { status?: number }).status = res.status;
    throw error;
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
 * Real user data is strictly returned from the database.
 * No mock or seeded data is ever shown to authenticated users.
 */
export async function getProducts(): Promise<ProductsResult> {
  const token = getStoredToken();
  if (!token) {
    // No token: return empty list
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
      5000,
    );
    const products = Array.isArray(data)
      ? data
      : ((data as { products?: Product[] }).products ?? []);
    return { products, source: "live" };
  } catch (err) {
    // Authenticated users must see their actual database data, never fake demo products
    console.error("Error fetching products from backend:", err);
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

export async function getFinanceSummary(): Promise<FinanceSummary> {
  const token = getStoredToken();
  if (!token) {
    return {
      total_revenue: 0,
      total_cost: 0,
      total_profit: 0,
      total_sales: 0,
      profit_margin: 0,
    };
  }
  return request<FinanceSummary>("/finance/summary");
}

export async function getExpenseBreakdown(): Promise<ExpenseItem[]> {
  const token = getStoredToken();
  if (!token) return [];
  return request<ExpenseItem[]>("/finance/expense-breakdown");
}

export async function getMonthlySummary(): Promise<MonthlySummaryItem[]> {
  const token = getStoredToken();
  if (!token) return [];
  return request<MonthlySummaryItem[]>("/finance/monthly-summary");
}

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const token = getStoredToken();
  if (!token) {
    return {
      total_revenue: 0,
      total_profit: 0,
      total_sales: 0,
      top_product: null,
      best_category: null,
      average_order_value: 0,
      repeat_customers_pct: 0,
    };
  }
  return request<AnalyticsSummary>("/analytics/summary");
}

export async function getAnalyticsTrend(range: string = "7d"): Promise<TrendPoint[]> {
  const token = getStoredToken();
  if (!token) return [];
  return request<TrendPoint[]>(`/analytics/trend?range=${encodeURIComponent(range)}`);
}

export async function getTopProducts(): Promise<TopProductItem[]> {
  const token = getStoredToken();
  if (!token) return [];
  return request<TopProductItem[]>("/analytics/top-products");
}

export async function getCategoryPerformance(): Promise<CategoryPerformanceItem[]> {
  const token = getStoredToken();
  if (!token) return [];
  return request<CategoryPerformanceItem[]>("/analytics/category-performance");
}

export async function getSales(limit?: number): Promise<SaleRecord[]> {
  const token = getStoredToken();
  if (!token) return [];
  const query = limit ? `?limit=${limit}` : "";
  return request<SaleRecord[]>(`/sales${query}`);
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
