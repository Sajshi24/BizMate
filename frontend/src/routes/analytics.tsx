import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { IndianRupee, ShoppingBag, TrendingUp, Users, Lightbulb } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { MetricCard } from "@/components/ui/metric-card";
import { Section } from "@/components/ui/section";
import { RevenueChart } from "@/components/charts/RevenueChart";
import { useProducts } from "@/hooks/useProducts";
import { revenueTrend } from "@/services/sample-data";
import { formatCompact, formatMoney } from "@/lib/format";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/analytics")({
  component: AnalyticsPage,
  head: () => ({
    meta: [
      { title: "Analytics — BizMate" },
      {
        name: "description",
        content: "Understand revenue trends, best sellers and category performance at a glance.",
      },
      { property: "og:title", content: "Analytics — BizMate" },
      { property: "og:description", content: "Revenue trends, best sellers and category performance." },
      { property: "og:url", content: "/analytics" },
    ],
    links: [{ rel: "canonical", href: "/analytics" }],
  }),
});

const ranges = [
  { key: "30d", label: "30 days" },
  { key: "12m", label: "12 months" },
] as const;

function AnalyticsPage() {
  const { data } = useProducts();
  const [range, setRange] = useState<(typeof ranges)[number]["key"]>("30d");
  const products = data?.products ?? [];
  const series = revenueTrend[range];

  const byCategory = Object.entries(
    products.reduce<Record<string, number>>((acc, p) => {
      acc[p.category] = (acc[p.category] ?? 0) + p.selling_price * Math.max(4, p.stock / 2);
      return acc;
    }, {}),
  )
    .map(([name, value]) => ({ name, value: Math.round(value) }))
    .sort((a, b) => b.value - a.value);

  const topProducts = [...products]
    .map((p) => ({ ...p, revenue: p.selling_price * Math.max(6, Math.round(p.stock * 0.9)) }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 5);

  const revenue = series.reduce((s, p) => s + p.revenue, 0);
  const sales = series.reduce((s, p) => s + p.sales, 0);

  return (
    <Page title="Analytics" subtitle="Where your revenue is coming from, and what's changing.">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Revenue" value={formatMoney(revenue)} change={12} context="vs previous period" icon={IndianRupee} />
        <MetricCard label="Orders" value={sales.toLocaleString()} change={8} context="completed sales" icon={ShoppingBag} />
        <MetricCard
          label="Average Order"
          value={formatMoney(Math.round(revenue / Math.max(1, sales)))}
          change={3.4}
          context="per customer"
          icon={TrendingUp}
        />
        <MetricCard label="Repeat Customers" value="38%" change={-1.2} context="of all orders" icon={Users} />
      </div>

      <Section
        className="mt-6"
        title="Revenue and sales trend"
        description="Combined view of value and volume"
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
        <RevenueChart data={series} />
      </Section>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Section title="Top selling products" description="By estimated revenue contribution">
          <div className="space-y-3.5">
            {topProducts.map((p, i) => {
              const share = (p.revenue / (topProducts[0]?.revenue || 1)) * 100;
              return (
                <div key={p.product_id}>
                  <div className="flex items-baseline justify-between gap-3">
                    <p className="truncate text-[13px] font-medium text-foreground">
                      <span className="num mr-2 text-muted-foreground">{i + 1}</span>
                      {p.name}
                    </p>
                    <span className="num shrink-0 text-[13px] text-muted-foreground">
                      {formatMoney(p.revenue)}
                    </span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-chart-1" style={{ width: `${share}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Section>

        <Section title="Category performance" description="Estimated revenue by category">
          <div className="h-[240px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byCategory} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }} />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  width={52}
                  tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
                  tickFormatter={(v) => formatCompact(v as number)}
                />
                <Tooltip
                  cursor={{ fill: "var(--color-muted)" }}
                  contentStyle={{
                    borderRadius: 10,
                    border: "1px solid var(--color-border)",
                    fontSize: 12,
                  }}
                  formatter={(v) => formatMoney(Number(v))}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={44}>
                  {byCategory.map((_, i) => (
                    <Cell key={i} fill={i === 0 ? "var(--color-chart-1)" : "var(--color-chart-2)"} fillOpacity={i === 0 ? 1 : 0.45} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Section>
      </div>

      <Section className="mt-6" title="What this means" description="Plain-language reading of your numbers">
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            `${byCategory[0]?.name ?? "Grains"} generated the highest revenue this month.`,
            "Sales increased by 12% compared to the previous period.",
            `${topProducts[0]?.name ?? "Your best seller"} alone drives close to a fifth of your takings — keep it stocked.`,
          ].map((text) => (
            <div key={text} className="flex gap-2.5 rounded-lg border border-border bg-muted/40 p-3.5">
              <Lightbulb className="mt-0.5 size-4 shrink-0 text-accent-foreground" strokeWidth={1.9} />
              <p className="text-[13px] leading-relaxed text-foreground">{text}</p>
            </div>
          ))}
        </div>
      </Section>
    </Page>
  );
}
