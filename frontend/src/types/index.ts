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
