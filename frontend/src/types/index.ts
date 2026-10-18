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
  cost?: number;
  profit?: number;
  date?: string;
}

export interface FinanceSummary {
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  total_sales: number;
  profit_margin: number;
}

export interface ExpenseItem {
  name: string;
  value: number;
}

export interface MonthlySummaryItem {
  month: string;
  label: string;
  revenue: number;
  expenses: number;
  profit: number;
}

export interface AnalyticsSummary {
  total_revenue: number;
  total_profit: number;
  total_sales: number;
  top_product: string | null;
  best_category: string | null;
  average_order_value: number;
  repeat_customers_pct: number;
}

export interface TopProductItem {
  product_id: string;
  product_name: string;
  quantity_sold: number;
  revenue: number;
}

export interface CategoryPerformanceItem {
  category: string;
  revenue: number;
  sales_count: number;
}

export interface SaleRecord {
  sale_id: string;
  user_id?: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_cost: number;
  unit_price: number;
  revenue: number;
  cost: number;
  profit: number;
  sale_date: string;
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
