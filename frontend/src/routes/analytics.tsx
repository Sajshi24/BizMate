import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { IndianRupee, ShoppingBag, TrendingUp, Users, Lightbulb } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { MetricCard } from "@/components/ui/metric-card";
import { Section } from "@/components/ui/section";
import { RevenueChart } from "@/components/charts/RevenueChart";
import {
  useAnalyticsSummary,
  useAnalyticsTrend,
  useTopProducts,
  useCategoryPerformance,
} from "@/hooks/useAnalytics";
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
      {
        property: "og:description",
        content: "Revenue trends, best sellers and category performance.",
      },
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
  const [range, setRange] = useState<(typeof ranges)[number]["key"]>("30d");
  const { data: trendData = [], isLoading: isTrendLoading } = useAnalyticsTrend(range);
  const { data: summary, isLoading: isSummaryLoading } = useAnalyticsSummary();
  const { data: topProductsData = [], isLoading: isTopProductsLoading } = useTopProducts();
  const { data: categoryData = [], isLoading: isCategoryLoading } = useCategoryPerformance();

  const series = trendData;
  const revenue = series.reduce((s, p) => s + p.revenue, 0);
  const sales = series.reduce((s, p) => s + p.sales, 0);
  const aov = sales > 0 ? Math.round(revenue / sales) : 0;
  const repeatPct = summary?.repeat_customers_pct ?? 0;

  const byCategory = categoryData.map((c) => ({
    name: c.category,
    value: c.revenue,
  }));

  const topProducts = topProductsData.slice(0, 5);

  return (
    <Page title="Analytics" subtitle="Where your revenue is coming from, and what's changing.">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Revenue"
          value={isTrendLoading ? "—" : formatMoney(revenue)}
          context={range === "30d" ? "last 30 days" : "last 12 months"}
          icon={IndianRupee}
          loading={isTrendLoading}
        />
        <MetricCard
          label="Orders"
          value={isTrendLoading ? "—" : sales.toLocaleString()}
          context="completed sales"
          icon={ShoppingBag}
          loading={isTrendLoading}
        />
        <MetricCard
          label="Average Order"
          value={isTrendLoading ? "—" : formatMoney(aov)}
          context="per transaction"
          icon={TrendingUp}
          loading={isTrendLoading}
        />
        <MetricCard
          label="Repeat Customers"
          value={isSummaryLoading ? "—" : `${repeatPct}%`}
          context="of all orders"
          icon={Users}
          loading={isSummaryLoading}
        />
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
          {isTopProductsLoading ? (
            <div className="space-y-3 p-4">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-6 w-full animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : topProducts.length === 0 ? (
            <div className="flex h-[200px] items-center justify-center text-center text-sm text-muted-foreground">
              No top selling products recorded yet.
            </div>
          ) : (
            <div className="space-y-3.5">
              {topProducts.map((p, i) => {
                const maxRevenue = topProducts[0]?.revenue || 1;
                const share = (p.revenue / maxRevenue) * 100;
                return (
                  <div key={p.product_id}>
                    <div className="flex items-baseline justify-between gap-3">
                      <p className="truncate text-[13px] font-medium text-foreground">
                        <span className="num mr-2 text-muted-foreground">{i + 1}</span>
                        {p.product_name}
                      </p>
                      <span className="num shrink-0 text-[13px] text-muted-foreground">
                        {formatMoney(p.revenue)}
                      </span>
                    </div>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-chart-1"
                        style={{ width: `${share}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Section>

        <Section title="Category performance" description="Revenue by category">
          <div className="h-[240px] w-full">
            {isCategoryLoading ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                Loading categories...
              </div>
            ) : byCategory.length === 0 ? (
              <div className="flex h-full items-center justify-center text-center text-sm text-muted-foreground">
                No category sales recorded yet.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byCategory} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid
                    stroke="var(--color-border)"
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="name"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
                  />
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
                      <Cell
                        key={i}
                        fill={i === 0 ? "var(--color-chart-1)" : "var(--color-chart-2)"}
                        fillOpacity={i === 0 ? 1 : 0.45}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Section>
      </div>

      <Section
        className="mt-6"
        title="What this means"
        description="Plain-language reading of your numbers"
      >
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            byCategory.length > 0 && byCategory[0]
              ? `${byCategory[0].name} generated the highest revenue (${formatMoney(byCategory[0].value)}) across categories.`
              : "No category performance data yet. As sales are logged, top categories will appear here.",
            sales > 0
              ? `${sales} order${sales > 1 ? "s" : ""} recorded in this period with an average value of ${formatMoney(aov)}.`
              : "No sales recorded for this period yet. Complete a transaction in Sales to track trends.",
            topProducts.length > 0 && topProducts[0]
              ? `${topProducts[0].product_name} is your best selling item (${formatMoney(topProducts[0].revenue)} total) — keep it well stocked.`
              : "Your best selling product will appear here once sales are logged.",
          ].map((text) => (
            <div
              key={text}
              className="flex gap-2.5 rounded-lg border border-border bg-muted/40 p-3.5"
            >
              <Lightbulb
                className="mt-0.5 size-4 shrink-0 text-accent-foreground"
                strokeWidth={1.9}
              />
              <p className="text-[13px] leading-relaxed text-foreground">{text}</p>
            </div>
          ))}
        </div>
      </Section>
    </Page>
  );
}
