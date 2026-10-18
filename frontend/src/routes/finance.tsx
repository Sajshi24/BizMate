import { createFileRoute } from "@tanstack/react-router";
import { IndianRupee, TrendingUp, Receipt, Percent } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { MetricCard } from "@/components/ui/metric-card";
import { Section } from "@/components/ui/section";
import { RevenueChart } from "@/components/charts/RevenueChart";
import { useFinanceSummary, useExpenseBreakdown } from "@/hooks/useFinance";
import { useAnalyticsTrend } from "@/hooks/useAnalytics";
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
  const { data: financeSummary, isLoading: isFinanceLoading } = useFinanceSummary();
  const { data: expenseBreakdown = [], isLoading: isExpenseLoading } = useExpenseBreakdown();
  const { data: trendData = [] } = useAnalyticsTrend("12m");

  const series = trendData;
  const revenue = financeSummary?.total_revenue ?? 0;
  const expenses = financeSummary?.total_cost ?? 0;
  const profit = financeSummary?.total_profit ?? 0;
  const margin = financeSummary?.profit_margin ?? 0;
  const totalExpense = expenseBreakdown.reduce((s, e) => s + e.value, 0);

  return (
    <Page title="Finance" subtitle="A clear picture of what you earn, spend and keep.">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Revenue"
          value={isFinanceLoading ? "—" : formatMoney(revenue)}
          context="lifetime takings"
          icon={IndianRupee}
          loading={isFinanceLoading}
        />
        <MetricCard
          label="Estimated Profit"
          value={isFinanceLoading ? "—" : formatMoney(profit)}
          context="after expenses"
          icon={TrendingUp}
          loading={isFinanceLoading}
        />
        <MetricCard
          label="Expenses"
          value={isFinanceLoading ? "—" : formatMoney(expenses)}
          context="direct product costs"
          icon={Receipt}
          loading={isFinanceLoading}
        />
        <MetricCard
          label="Profit Margin"
          value={isFinanceLoading ? "—" : `${margin}%`}
          context="of revenue"
          icon={Percent}
          loading={isFinanceLoading}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Section
          className="lg:col-span-2"
          title="Revenue and profit trend"
          description="Monthly performance across the year"
        >
          <RevenueChart data={series} showSales={false} />
        </Section>

        <Section title="Expense breakdown" description="Where your money goes by category">
          {isExpenseLoading ? (
            <div className="space-y-3 p-4">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-6 w-full animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : expenseBreakdown.length === 0 ? (
            <div className="flex h-[200px] items-center justify-center text-center text-sm text-muted-foreground">
              No expenses recorded yet.
            </div>
          ) : (
            <div className="space-y-4">
              {expenseBreakdown.map((e) => {
                const pct = totalExpense > 0 ? (e.value / totalExpense) * 100 : 0;
                return (
                  <div key={e.name}>
                    <div className="flex items-baseline justify-between">
                      <span className="text-[13px] font-medium text-foreground">{e.name}</span>
                      <span className="num text-[13px] text-muted-foreground">
                        {formatMoney(e.value)}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-chart-1"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="num w-10 text-right text-[11.5px] text-muted-foreground">
                        {pct.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
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
              {series
                .slice(-6)
                .reverse()
                .map((m) => {
                  const exp = m.cost ?? 0;
                  const prof = m.profit ?? 0;
                  return (
                    <tr
                      key={m.label}
                      className="border-b border-border/70 transition-colors last:border-0 hover:bg-muted/50"
                    >
                      <td className="px-5 py-3.5 text-[13px] font-medium text-foreground">
                        {m.label}
                      </td>
                      <td className="num px-5 py-3.5 text-right text-[13px] text-foreground">
                        {formatMoney(m.revenue)}
                      </td>
                      <td className="num px-5 py-3.5 text-right text-[13px] text-muted-foreground">
                        {formatMoney(exp)}
                      </td>
                      <td className="num px-5 py-3.5 text-right text-[13px] font-medium text-success">
                        {formatMoney(prof)}
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
