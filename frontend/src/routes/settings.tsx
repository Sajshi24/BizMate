import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/layout/Page";
import { Section } from "@/components/ui/section";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { API_URL } from "@/services/api";
import { toast } from "sonner";

export const Route = createFileRoute("/settings")({
  component: SettingsPage,
  head: () => ({
    meta: [
      { title: "Settings — BizMate" },
      {
        name: "description",
        content: "Update your business profile, alert preferences and connection settings.",
      },
      { property: "og:title", content: "Settings — BizMate" },
      { property: "og:description", content: "Manage your business profile and preferences." },
      { property: "og:url", content: "/settings" },
    ],
    links: [{ rel: "canonical", href: "/settings" }],
  }),
});

function SettingsPage() {
  return (
    <Page
      title="Settings"
      subtitle="Your business profile and preferences."
      action={
        <Button size="sm" className="h-9" onClick={() => toast.success("Settings saved")}>
          Save changes
        </Button>
      }
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Business profile">
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="biz">Business name</Label>
              <Input id="biz" defaultValue="Balte General Store" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="owner">Owner name</Label>
              <Input id="owner" defaultValue="Sakshi Balte" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Contact email</Label>
              <Input id="email" type="email" placeholder="you@yourbusiness.com" />
            </div>
          </div>
        </Section>

        <Section title="Alerts" description="Choose what BizMate tells you about">
          <div className="space-y-4">
            {[
              { label: "Low stock alerts", hint: "When a product drops below its minimum" },
              { label: "Daily sales summary", hint: "A short recap at the end of each day" },
              { label: "Weekly business insights", hint: "Trends and suggestions every Monday" },
            ].map((s, i) => (
              <div key={s.label} className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[13px] font-medium text-foreground">{s.label}</p>
                  <p className="text-[12px] text-muted-foreground">{s.hint}</p>
                </div>
                <Switch defaultChecked={i < 2} />
              </div>
            ))}
          </div>
        </Section>

        <Section title="Connection" description="Where BizMate reads your business data from">
          <div className="space-y-1.5">
            <Label htmlFor="api">Business service address</Label>
            <Input id="api" defaultValue={API_URL} readOnly className="text-muted-foreground" />
            <p className="pt-1 text-[12px] text-muted-foreground">
              When this service isn't reachable, BizMate shows sample data so you can still explore
              every screen.
            </p>
          </div>
        </Section>
      </div>
    </Page>
  );
}
