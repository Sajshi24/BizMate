import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Search, Minus, Plus, X, CheckCircle2, ShoppingCart } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Section, EmptyState } from "@/components/ui/section";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useProducts } from "@/hooks/useProducts";
import { api } from "@/services/api";
import { formatMoney, stockStatus } from "@/lib/format";
import type { CartLine, Product } from "@/types";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export const Route = createFileRoute("/sales")({
  component: SalesPage,
  head: () => ({
    meta: [
      { title: "Sales — BizMate" },
      {
        name: "description",
        content: "Record a sale in seconds with a fast, simple point-of-sale workflow.",
      },
      { property: "og:title", content: "Sales — BizMate" },
      { property: "og:description", content: "Record sales quickly and keep stock in sync." },
      { property: "og:url", content: "/sales" },
    ],
    links: [{ rel: "canonical", href: "/sales" }],
  }),
});

function SalesPage() {
  const { data, isLoading } = useProducts();
  const products = data?.products ?? [];
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("All");
  const [lines, setLines] = useState<CartLine[]>([]);
  const [discount, setDiscount] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState<{ total: number; items: number } | null>(null);

  const categories = useMemo(
    () => ["All", ...Array.from(new Set(products.map((p) => p.category))).sort()],
    [products],
  );

  const visible = products.filter(
    (p) =>
      (category === "All" || p.category === category) &&
      p.name.toLowerCase().includes(q.toLowerCase()),
  );

  const add = (product: Product) => {
    setDone(null);
    setLines((prev) => {
      const found = prev.find((l) => l.product.product_id === product.product_id);
      if (found)
        return prev.map((l) =>
          l.product.product_id === product.product_id
            ? { ...l, qty: Math.min(l.qty + 1, product.stock) }
            : l,
        );
      return [...prev, { product, qty: 1 }];
    });
  };

  const setQty = (id: string, delta: number) =>
    setLines((prev) =>
      prev
        .map((l) =>
          l.product.product_id === id
            ? { ...l, qty: Math.max(0, Math.min(l.qty + delta, l.product.stock)) }
            : l,
        )
        .filter((l) => l.qty > 0),
    );

  const subtotal = lines.reduce((s, l) => s + l.product.selling_price * l.qty, 0);
  const discountValue = Math.round((subtotal * discount) / 100);
  const total = subtotal - discountValue;

  const complete = async () => {
    setSubmitting(true);
    try {
      await api.recordSale(lines.map((l) => ({ product_id: l.product.product_id, qty: l.qty })));
      setDone({ total, items: lines.reduce((s, l) => s + l.qty, 0) });
      setLines([]);
      setDiscount(0);
      toast.success("Sale recorded", { description: `${formatMoney(total)} added to today's takings.` });
    } catch {
      toast.error("We couldn't record that sale", { description: "Please try again in a moment." });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Page title="Sales" subtitle="Record a sale in a few taps.">
      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <Section
          bodyClassName="p-4"
          title="Choose products"
          description="Tap a product to add it to the sale"
          action={
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search products"
                className="h-9 w-full pl-8 sm:w-56"
              />
            </div>
          }
        >
          <div className="mb-4 flex flex-wrap gap-1.5">
            {categories.map((c) => (
              <button
                key={c}
                onClick={() => setCategory(c)}
                className={cn(
                  "rounded-full border px-3 py-1.5 text-[12px] font-medium transition-colors",
                  category === c
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border text-muted-foreground hover:bg-muted",
                )}
              >
                {c}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-[92px] rounded-xl" />
              ))}
            </div>
          ) : visible.length === 0 ? (
            <EmptyState title="No products found" description="Try a different search or category." />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {visible.map((p) => {
                const status = stockStatus(p);
                const out = p.stock === 0;
                return (
                  <button
                    key={p.product_id}
                    disabled={out}
                    onClick={() => add(p)}
                    className={cn(
                      "group rounded-xl border border-border p-3.5 text-left transition-all duration-200",
                      out
                        ? "cursor-not-allowed opacity-50"
                        : "hover:border-primary/30 hover:shadow-[var(--shadow-raised)]",
                    )}
                  >
                    <p className="line-clamp-2 text-[13.5px] font-medium text-foreground">{p.name}</p>
                    <p className="mt-0.5 text-[12px] text-muted-foreground">{p.category}</p>
                    <div className="mt-3 flex items-center justify-between">
                      <span className="num text-[14px] font-semibold text-foreground">
                        {formatMoney(p.selling_price)}
                      </span>
                      <span
                        className={cn(
                          "text-[11.5px] font-medium",
                          status === "healthy"
                            ? "text-muted-foreground"
                            : status === "low"
                              ? "text-warning"
                              : "text-destructive",
                        )}
                      >
                        {p.stock} in stock
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </Section>

        <div className="lg:sticky lg:top-24 lg:self-start">
          <Section title="Current sale" description={`${lines.length} item${lines.length === 1 ? "" : "s"}`} bodyClassName="p-4">
            {done ? (
              <div className="flex flex-col items-center py-8 text-center">
                <CheckCircle2 className="size-9 text-success" strokeWidth={1.6} />
                <p className="mt-3 text-[15px] font-semibold text-foreground">Sale completed</p>
                <p className="mt-1 text-[13px] text-muted-foreground">
                  {done.items} item{done.items === 1 ? "" : "s"} · {formatMoney(done.total)}
                </p>
                <Button className="mt-5" size="sm" onClick={() => setDone(null)}>
                  Start a new sale
                </Button>
              </div>
            ) : lines.length === 0 ? (
              <EmptyState
                icon={<ShoppingCart className="size-6" />}
                title="No products yet"
                description="Pick products on the left to build this sale."
              />
            ) : (
              <>
                <div className="space-y-2">
                  {lines.map((l) => (
                    <div
                      key={l.product.product_id}
                      className="rounded-lg border border-border p-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-[13px] font-medium text-foreground">{l.product.name}</p>
                        <button
                          onClick={() => setQty(l.product.product_id, -l.qty)}
                          className="rounded p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-destructive"
                          aria-label={`Remove ${l.product.name}`}
                        >
                          <X className="size-3.5" />
                        </button>
                      </div>
                      <div className="mt-2.5 flex items-center justify-between">
                        <div className="flex items-center gap-1 rounded-lg border border-border">
                          <button
                            onClick={() => setQty(l.product.product_id, -1)}
                            className="p-1.5 text-muted-foreground hover:text-foreground"
                            aria-label="Decrease quantity"
                          >
                            <Minus className="size-3.5" />
                          </button>
                          <span className="num w-6 text-center text-[13px] font-medium">{l.qty}</span>
                          <button
                            onClick={() => setQty(l.product.product_id, 1)}
                            className="p-1.5 text-muted-foreground hover:text-foreground"
                            aria-label="Increase quantity"
                          >
                            <Plus className="size-3.5" />
                          </button>
                        </div>
                        <span className="num text-[13.5px] font-semibold text-foreground">
                          {formatMoney(l.product.selling_price * l.qty)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-4 space-y-2 border-t border-border pt-4 text-[13px]">
                  <div className="flex justify-between text-muted-foreground">
                    <span>Subtotal</span>
                    <span className="num">{formatMoney(subtotal)}</span>
                  </div>
                  <div className="flex items-center justify-between text-muted-foreground">
                    <span>Discount</span>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        value={discount}
                        onChange={(e) =>
                          setDiscount(Math.min(100, Math.max(0, Number(e.target.value))))
                        }
                        className="h-8 w-16 text-right"
                      />
                      <span className="num w-20 text-right">−{formatMoney(discountValue)}</span>
                    </div>
                  </div>
                  <div className="flex justify-between border-t border-border pt-3 text-[15px] font-semibold text-foreground">
                    <span>Total</span>
                    <span className="num">{formatMoney(total)}</span>
                  </div>
                </div>

                <Button className="mt-4 w-full" onClick={complete} disabled={submitting}>
                  {submitting ? "Recording…" : "Complete Sale"}
                </Button>
              </>
            )}
          </Section>
        </div>
      </div>
    </Page>
  );
}
