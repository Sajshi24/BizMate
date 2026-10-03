export interface Product {
  product_id: string;
  name: string;
  category: string;
  cost_price: number;
  selling_price: number;
  stock: number;
  minimum_stock: number;
  supplier: string;
}

export type StockStatus = "healthy" | "low" | "critical";

export interface CartLine {
  product: Product;
  qty: number;
}

export interface TrendPoint {
  label: string;
  revenue: number;
  sales: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  store_name: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  store_name?: string;
}
