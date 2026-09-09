import { createFileRoute } from "@tanstack/react-router";
import { IndianRupee, TrendingUp, Receipt, Percent } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { MetricCard } from "@/components/ui/metric-card";
import { Section } from "@/components/ui/section";
import { RevenueChart } from "@/components/charts/RevenueChart";
import { expenseBreakdown, revenueTrend } from "@/services/sample-data";
import { formatMoney } from "@/lib/format";

export const Route = createFileRoute("/finance")({
  component: FinancePage,
  head: () => ({
    meta: [
      { title: "Finance — BizMate" },
      {
        name: "description",
        content: "Track revenue, profit, expenses and margins with a clear financial overview.",
      },
      { property: "og:title", content: "Finance — BizMate" },
      { property: "og:description", content: "Revenue, profit, expenses and margins in one view." },
      { property: "og:url", content: "/finance" },
    ],
    links: [{ rel: "canonical", href: "/finance" }],
  }),
});

function FinancePage() {
  const series = revenueTrend["12m"];
  const revenue = series.reduce((s, p) => s + p.revenue, 0);
  const expenses = expenseBreakdown.reduce((s, e) => s + e.value, 0) * 10;
  const profit = revenue - expenses;
  const margin = ((profit / revenue) * 100).toFixed(1);
  const totalExpense = expenseBreakdown.reduce((s, e) => s + e.value, 0);

  return (
    <Page title="Finance" subtitle="A clear picture of what you earn, spend and keep.">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Revenue" value={formatMoney(revenue)} change={11.2} context="last 12 months" icon={IndianRupee} />
        <MetricCard label="Estimated Profit" value={formatMoney(profit)} change={6.8} context="after expenses" icon={TrendingUp} />
        <MetricCard label="Expenses" value={formatMoney(expenses)} change={-2.1} context="last 12 months" icon={Receipt} />
        <MetricCard label="Profit Margin" value={`${margin}%`} change={1.4} context="of revenue" icon={Percent} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Section className="lg:col-span-2" title="Revenue and profit trend" description="Monthly performance across the year">
          <RevenueChart data={series} showSales={false} />
        </Section>

        <Section title="Expense breakdown" description="Where your money goes each month">
          <div className="space-y-4">
            {expenseBreakdown.map((e) => {
              const pct = (e.value / totalExpense) * 100;
              return (
                <div key={e.name}>
                  <div className="flex items-baseline justify-between">
                    <span className="text-[13px] font-medium text-foreground">{e.name}</span>
                    <span className="num text-[13px] text-muted-foreground">{formatMoney(e.value)}</span>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                      <div className="h-full rounded-full bg-chart-1" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="num w-10 text-right text-[11.5px] text-muted-foreground">
                      {pct.toFixed(0)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </Section>
      </div>

      <Section className="mt-6" title="Monthly summary" bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left">
            <thead>
              <tr className="border-b border-border text-[11.5px] uppercase tracking-wide text-muted-foreground">
                <th className="px-5 py-3 font-medium">Month</th>
                <th className="px-5 py-3 text-right font-medium">Revenue</th>
                <th className="px-5 py-3 text-right font-medium">Expenses</th>
                <th className="px-5 py-3 text-right font-medium">Profit</th>
              </tr>
            </thead>
            <tbody>
              {series.slice(-6).reverse().map((m) => {
                const exp = Math.round(m.revenue * 0.72);
                return (
                  <tr key={m.label} className="border-b border-border/70 transition-colors last:border-0 hover:bg-muted/50">
                    <td className="px-5 py-3.5 text-[13px] font-medium text-foreground">{m.label}</td>
                    <td className="num px-5 py-3.5 text-right text-[13px] text-foreground">{formatMoney(m.revenue)}</td>
                    <td className="num px-5 py-3.5 text-right text-[13px] text-muted-foreground">{formatMoney(exp)}</td>
                    <td className="num px-5 py-3.5 text-right text-[13px] font-medium text-success">
                      {formatMoney(m.revenue - exp)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Section>
    </Page>
  );
}
