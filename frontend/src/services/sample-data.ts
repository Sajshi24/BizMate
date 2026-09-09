import type { Product, TrendPoint } from "@/types";

export const sampleProducts: Product[] = [
  { product_id: "p1", name: "Basmati Rice 5kg", category: "Grains", cost_price: 180, selling_price: 250, stock: 45, minimum_stock: 10, supplier: "Star Foods Co." },
  { product_id: "p2", name: "Full Cream Milk 1L", category: "Dairy", cost_price: 42, selling_price: 58, stock: 4, minimum_stock: 12, supplier: "Green Valley Dairy" },
  { product_id: "p3", name: "Hand Sanitizer 200ml", category: "Household", cost_price: 55, selling_price: 90, stock: 2, minimum_stock: 15, supplier: "PureCare Ltd." },
  { product_id: "p4", name: "Whole Wheat Atta 10kg", category: "Grains", cost_price: 320, selling_price: 420, stock: 28, minimum_stock: 8, supplier: "Star Foods Co." },
  { product_id: "p5", name: "Sunflower Oil 1L", category: "Cooking", cost_price: 118, selling_price: 155, stock: 34, minimum_stock: 10, supplier: "Golden Harvest" },
  { product_id: "p6", name: "Detergent Powder 2kg", category: "Household", cost_price: 190, selling_price: 265, stock: 19, minimum_stock: 6, supplier: "PureCare Ltd." },
  { product_id: "p7", name: "Greek Yoghurt 400g", category: "Dairy", cost_price: 62, selling_price: 95, stock: 11, minimum_stock: 10, supplier: "Green Valley Dairy" },
  { product_id: "p8", name: "Masala Tea 500g", category: "Beverages", cost_price: 210, selling_price: 299, stock: 52, minimum_stock: 12, supplier: "Hillside Estates" },
  { product_id: "p9", name: "Instant Coffee 100g", category: "Beverages", cost_price: 245, selling_price: 340, stock: 7, minimum_stock: 8, supplier: "Hillside Estates" },
  { product_id: "p10", name: "Toor Dal 2kg", category: "Grains", cost_price: 220, selling_price: 285, stock: 41, minimum_stock: 10, supplier: "Star Foods Co." },
  { product_id: "p11", name: "Bath Soap Pack of 4", category: "Household", cost_price: 130, selling_price: 180, stock: 63, minimum_stock: 15, supplier: "PureCare Ltd." },
  { product_id: "p12", name: "Paneer 200g", category: "Dairy", cost_price: 75, selling_price: 110, stock: 16, minimum_stock: 10, supplier: "Green Valley Dairy" },
];

export const revenueTrend: Record<"7d" | "30d" | "12m", TrendPoint[]> = {
  "7d": [
    { label: "Mon", revenue: 12400, sales: 38 },
    { label: "Tue", revenue: 14100, sales: 44 },
    { label: "Wed", revenue: 11800, sales: 35 },
    { label: "Thu", revenue: 16250, sales: 51 },
    { label: "Fri", revenue: 19800, sales: 62 },
    { label: "Sat", revenue: 24300, sales: 78 },
    { label: "Sun", revenue: 21100, sales: 69 },
  ],
  "30d": Array.from({ length: 30 }, (_, i) => ({
    label: `${i + 1}`,
    revenue: 9500 + Math.round(Math.sin(i / 2.4) * 3200 + i * 210 + (i % 5) * 640),
    sales: 28 + Math.round(Math.sin(i / 2.1) * 9 + i * 0.6),
  })),
  "12m": [
    { label: "Oct", revenue: 268000, sales: 842 },
    { label: "Nov", revenue: 295000, sales: 908 },
    { label: "Dec", revenue: 361000, sales: 1104 },
    { label: "Jan", revenue: 302000, sales: 946 },
    { label: "Feb", revenue: 288000, sales: 901 },
    { label: "Mar", revenue: 318000, sales: 988 },
    { label: "Apr", revenue: 335000, sales: 1032 },
    { label: "May", revenue: 349000, sales: 1078 },
    { label: "Jun", revenue: 327000, sales: 1005 },
    { label: "Jul", revenue: 358000, sales: 1112 },
    { label: "Aug", revenue: 384000, sales: 1188 },
    { label: "Sep", revenue: 402000, sales: 1243 },
  ],
};

export const expenseBreakdown = [
  { name: "Stock purchases", value: 214000 },
  { name: "Rent", value: 48000 },
  { name: "Staff", value: 62000 },
  { name: "Utilities", value: 17500 },
  { name: "Other", value: 9800 },
];
