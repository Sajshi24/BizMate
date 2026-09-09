import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Package, Search, ArrowUpDown, MoreHorizontal, PackageX, RefreshCw } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { PrimaryAction } from "@/components/layout/PageHeader";
import { Section, EmptyState } from "@/components/ui/section";
import { StatusBadge } from "@/components/ui/status-badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProducts } from "@/hooks/useProducts";
import { formatMoney, stockStatus } from "@/lib/format";
import { toast } from "sonner";

export const Route = createFileRoute("/inventory")({
  component: InventoryPage,
  head: () => ({
    meta: [
      { title: "Inventory — BizMate" },
      {
        name: "description",
        content: "Monitor your products, suppliers and stock levels, and spot low stock early.",
      },
      { property: "og:title", content: "Inventory — BizMate" },
      {
        property: "og:description",
        content: "Monitor your products and keep your stock healthy.",
      },
      { property: "og:url", content: "/inventory" },
    ],
    links: [{ rel: "canonical", href: "/inventory" }],
  }),
});

type SortKey = "name" | "stock" | "selling_price";

function InventoryPage() {
  const { data, isLoading, isError, refetch, isFetching } = useProducts();
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState<SortKey>("name");

  const products = data?.products ?? [];
  const categories = useMemo(
    () => Array.from(new Set(products.map((p) => p.category))).sort(),
    [products],
  );

  const rows = useMemo(() => {
    return products
      .filter(
        (p) =>
          (category === "all" || p.category === category) &&
          (p.name.toLowerCase().includes(q.toLowerCase()) ||
            p.supplier.toLowerCase().includes(q.toLowerCase())),
      )
      .sort((a, b) =>
        sort === "name" ? a.name.localeCompare(b.name) : Number(b[sort]) - Number(a[sort]),
      );
  }, [products, q, category, sort]);

  const counts = {
    total: products.length,
    healthy: products.filter((p) => stockStatus(p) === "healthy").length,
    low: products.filter((p) => stockStatus(p) === "low").length,
    critical: products.filter((p) => stockStatus(p) === "critical").length,
  };

  return (
    <Page
      title="Inventory"
      subtitle="Monitor your products and keep your stock healthy."
      action={
        <PrimaryAction onClick={() => toast("Add product", { description: "Product intake opens once your catalogue service is connected." })}>
          Add Product
        </PrimaryAction>
      }
    >
      <div className="panel grid grid-cols-2 divide-border sm:grid-cols-4 sm:divide-x">
        {[
          { label: "Total Products", value: counts.total },
          { label: "Healthy Stock", value: counts.healthy },
          { label: "Low Stock", value: counts.low },
          { label: "Critical Stock", value: counts.critical },
        ].map((s) => (
          <div key={s.label} className="p-5">
            <p className="text-[12px] font-medium uppercase tracking-wide text-muted-foreground">
              {s.label}
            </p>
            <p className="num mt-2 text-[24px] font-semibold leading-none text-foreground">
              {isLoading ? "—" : s.value}
            </p>
          </div>
        ))}
      </div>

      <Section
        className="mt-6"
        bodyClassName="p-0"
        title="Products"
        description={`${rows.length} of ${products.length} products`}
        action={
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search products"
                className="h-9 w-full pl-8 sm:w-56"
              />
            </div>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="h-9 w-[150px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All categories</SelectItem>
                {categories.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sort} onValueChange={(v) => setSort(v as SortKey)}>
              <SelectTrigger className="h-9 w-[150px]">
                <ArrowUpDown className="size-3.5 text-muted-foreground" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Name A–Z</SelectItem>
                <SelectItem value="stock">Highest stock</SelectItem>
                <SelectItem value="selling_price">Highest price</SelectItem>
              </SelectContent>
            </Select>
          </div>
        }
      >
        {isLoading ? (
          <div className="space-y-2 p-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        ) : isError ? (
          <div className="p-5">
            <EmptyState
              icon={<PackageX className="size-6" />}
              title="We couldn't load your products"
              description="The business service didn't respond. Check that it's running and try again."
              action={
                <Button variant="outline" size="sm" onClick={() => refetch()}>
                  <RefreshCw className="mr-1.5 size-3.5" /> Try again
                </Button>
              }
            />
          </div>
        ) : rows.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={<Package className="size-6" />}
              title="No products match your filters"
              description="Try a different search term or clear the category filter."
              action={
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setQ("");
                    setCategory("all");
                  }}
                >
                  Clear filters
                </Button>
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left">
              <thead>
                <tr className="border-b border-border text-[11.5px] uppercase tracking-wide text-muted-foreground">
                  <th className="px-5 py-3 font-medium">Product</th>
                  <th className="px-5 py-3 font-medium">Category</th>
                  <th className="px-5 py-3 text-right font-medium">Cost</th>
                  <th className="px-5 py-3 text-right font-medium">Selling</th>
                  <th className="px-5 py-3 text-right font-medium">Stock</th>
                  <th className="px-5 py-3 font-medium">Supplier</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody>
                {rows.map((p) => (
                  <tr
                    key={p.product_id}
                    className="border-b border-border/70 transition-colors last:border-0 hover:bg-muted/50"
                  >
                    <td className="px-5 py-3.5">
                      <p className="text-[13.5px] font-medium text-foreground">{p.name}</p>
                      <p className="text-[12px] text-muted-foreground">
                        Min. {p.minimum_stock} units
                      </p>
                    </td>
                    <td className="px-5 py-3.5 text-[13px] text-muted-foreground">{p.category}</td>
                    <td className="num px-5 py-3.5 text-right text-[13px] text-muted-foreground">
                      {formatMoney(p.cost_price)}
                    </td>
                    <td className="num px-5 py-3.5 text-right text-[13px] font-medium text-foreground">
                      {formatMoney(p.selling_price)}
                    </td>
                    <td className="num px-5 py-3.5 text-right text-[13px] text-foreground">
                      {p.stock}
                    </td>
                    <td className="px-5 py-3.5 text-[13px] text-muted-foreground">{p.supplier}</td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={stockStatus(p)} />
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => toast(p.name, { description: "Product editing arrives with the next release." })}
                        className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                        aria-label={`Actions for ${p.name}`}
                      >
                        <MoreHorizontal className="size-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {isFetching && !isLoading && (
          <p className="border-t border-border px-5 py-2 text-[12px] text-muted-foreground">
            Refreshing…
          </p>
        )}
      </Section>
    </Page>
  );
}
