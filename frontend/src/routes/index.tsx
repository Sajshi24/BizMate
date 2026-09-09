import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  IndianRupee,
  ShoppingBag,
  Boxes,
  AlertTriangle,
  ArrowRight,
  Plus,
  Megaphone,
  Sparkles,
  ShoppingCart,
} from "lucide-react";
import { Page } from "@/components/layout/Page";
import { PrimaryAction } from "@/components/layout/PageHeader";
import { MetricCard } from "@/components/ui/metric-card";
import { Section, EmptyState } from "@/components/ui/section";
import { RevenueChart } from "@/components/charts/RevenueChart";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useProducts } from "@/hooks/useProducts";
import { revenueTrend } from "@/services/sample-data";
import { formatMoney, stockStatus } from "@/lib/format";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  component: Dashboard,
  head: () => ({
    meta: [
      { title: "Dashboard — BizMate" },
      {
        name: "description",
        content:
          "See how your business is performing today: revenue, sales, stock health and what needs your attention.",
      },
      { property: "og:title", content: "Dashboard — BizMate" },
      {
        property: "og:description",
        content: "See revenue, sales, stock health and what needs your attention.",
      },
      { property: "og:url", content: "/" },
    ],
    links: [{ rel: "canonical", href: "/" }],
  }),
});

const ranges = [
  { key: "7d", label: "7 days" },
  { key: "30d", label: "30 days" },
  { key: "12m", label: "12 months" },
] as const;

function Dashboard() {
  const { data, isLoading } = useProducts();
  const [range, setRange] = useState<(typeof ranges)[number]["key"]>("7d");
  const products = data?.products ?? [];

  const series = revenueTrend[range];
  const revenue = series.reduce((s, p) => s + p.revenue, 0);
  const sales = series.reduce((s, p) => s + p.sales, 0);
  const inStock = products.reduce((s, p) => s + p.stock, 0);
  const needsAttention = products
    .filter((p) => stockStatus(p) !== "healthy")
    .sort((a, b) => a.stock - b.stock);

  return (
    <Page
      title="Dashboard"
      subtitle="Here's what's happening with your business today."
      action={
        <Link to="/sales">
          <PrimaryAction>Record Sale</PrimaryAction>
        </Link>
      }
    >
      <div className="panel mb-6 flex flex-wrap items-center justify-between gap-4 p-6">
        <div>
          <h2 className="text-[20px] font-semibold tracking-tight text-foreground">
            Good morning, Sakshi
          </h2>
          <p className="mt-1 max-w-2xl text-[13.5px] text-muted-foreground">
            Your sales are performing well this week
            {needsAttention.length > 0 ? (
              <>
                , but{" "}
                <span className="font-medium text-foreground">
                  {needsAttention.length} product{needsAttention.length > 1 ? "s" : ""}
                </span>{" "}
                need restocking.
              </>
            ) : (
              " and every product is comfortably in stock."
            )}
          </p>
        </div>
        {data?.source === "demo" && (
          <span className="rounded-full bg-muted px-3 py-1 text-[11.5px] font-medium text-muted-foreground">
            Showing sample data — business service offline
          </span>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Total Revenue"
          value={formatMoney(revenue)}
          change={12.4}
          context="vs previous period"
          icon={IndianRupee}
        />
        <MetricCard
          label="Total Sales"
          value={sales.toLocaleString()}
          change={8.1}
          context="orders completed"
          icon={ShoppingBag}
        />
        <MetricCard
          label="Products in Stock"
          value={isLoading ? "—" : inStock.toLocaleString()}
          context={`${products.length} products tracked`}
          icon={Boxes}
          loading={isLoading}
        />
        <MetricCard
          label="Low Stock Items"
          value={isLoading ? "—" : String(needsAttention.length)}
          context="need reordering"
          icon={AlertTriangle}
          tone={needsAttention.length ? "warning" : "neutral"}
          loading={isLoading}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Section
          className="lg:col-span-2"
          title="Business performance"
          description="Revenue and sales volume over time"
          action={
            <div className="flex rounded-lg border border-border bg-muted/60 p-0.5">
              {ranges.map((r) => (
                <button
                  key={r.key}
                  onClick={() => setRange(r.key)}
                  className={cn(
                    "rounded-[7px] px-3 py-1.5 text-[12px] font-medium transition-colors",
                    range === r.key
                      ? "bg-card text-foreground shadow-[var(--shadow-card)]"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {r.label}
                </button>
              ))}
            </div>
          }
        >
          <div className="mb-4 flex gap-6 text-[12px] text-muted-foreground">
            <span className="flex items-center gap-2">
              <span className="h-0.5 w-4 rounded bg-chart-1" /> Revenue
            </span>
            <span className="flex items-center gap-2">
              <span className="h-0.5 w-4 rounded bg-chart-2" /> Sales
            </span>
          </div>
          <RevenueChart data={series} />
        </Section>

        <Section
          title="Attention required"
          description="Issues worth acting on today"
          bodyClassName="p-4"
        >
          {isLoading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-16 w-full rounded-lg" />
              ))}
            </div>
          ) : needsAttention.length === 0 ? (
            <EmptyState
              title="Nothing needs attention"
              description="Every product is above its minimum stock level."
            />
          ) : (
            <div className="space-y-2">
              {needsAttention.slice(0, 4).map((p) => {
                const critical = stockStatus(p) === "critical";
                return (
                  <div
                    key={p.product_id}
                    className="rounded-lg border border-border p-3 transition-colors hover:bg-muted/50"
                  >
                    <div className="flex items-start gap-2.5">
                      <AlertTriangle
                        className={cn(
                          "mt-0.5 size-4 shrink-0",
                          critical ? "text-destructive" : "text-warning",
                        )}
                        strokeWidth={1.9}
                      />
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-medium text-foreground">
                          {p.name} {critical ? "stock is critical" : "is running low"}
                        </p>
                        <p className="text-[12px] text-muted-foreground">
                          Only {p.stock} unit{p.stock === 1 ? "" : "s"} remaining
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
              <Link to="/inventory" className="block pt-1">
                <Button variant="outline" size="sm" className="w-full">
                  View Inventory <ArrowRight className="ml-1 size-3.5" />
                </Button>
              </Link>
            </div>
          )}
        </Section>
      </div>

      <Section className="mt-6" title="Quick actions" bodyClassName="p-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[
            { to: "/sales", icon: ShoppingCart, label: "Record a Sale", hint: "Ring up a new order" },
            { to: "/inventory", icon: Plus, label: "Add Product", hint: "Expand your catalogue" },
            { to: "/marketing", icon: Megaphone, label: "Create Promotion", hint: "Generate campaign copy" },
            { to: "/advisor", icon: Sparkles, label: "Ask BizMate AI", hint: "Get business advice" },
          ].map((a) => (
            <Link
              key={a.to + a.label}
              to={a.to}
              className="group flex items-center gap-3 rounded-lg border border-border p-3.5 transition-all duration-200 hover:border-primary/30 hover:shadow-[var(--shadow-raised)]"
            >
              <span className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <a.icon className="size-[18px]" strokeWidth={1.8} />
              </span>
              <span className="min-w-0">
                <span className="block truncate text-[13px] font-medium text-foreground">
                  {a.label}
                </span>
                <span className="block truncate text-[12px] text-muted-foreground">{a.hint}</span>
              </span>
              <ArrowRight className="ml-auto size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
          ))}
        </div>
      </Section>
    </Page>
  );
}
