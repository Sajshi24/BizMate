import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Copy, RefreshCw, Pencil, Sparkles, Check } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Section, EmptyState } from "@/components/ui/section";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProducts } from "@/hooks/useProducts";
import { api } from "@/services/api";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export const Route = createFileRoute("/marketing")({
  component: MarketingPage,
  head: () => ({
    meta: [
      { title: "Marketing — BizMate" },
      {
        name: "description",
        content: "Create promotional posts, posters and offers for your products in a few steps.",
      },
      { property: "og:title", content: "Marketing — BizMate" },
      { property: "og:description", content: "Create campaign content for your products in minutes." },
      { property: "og:url", content: "/marketing" },
    ],
    links: [{ rel: "canonical", href: "/marketing" }],
  }),
});

const campaignTypes = [
  { key: "Instagram Post", hint: "Short, friendly caption with hashtags" },
  { key: "Promotional Poster", hint: "Bold headline and offer text" },
  { key: "Product Advertisement", hint: "Benefit-led product copy" },
  { key: "Festival Offer", hint: "Seasonal greeting with a deal" },
];

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-border p-5 last:border-0">
      <div className="mb-3 flex items-center gap-2.5">
        <span className="flex size-6 items-center justify-center rounded-full bg-accent text-[11.5px] font-semibold text-accent-foreground">
          {n}
        </span>
        <h3 className="text-[13.5px] font-semibold text-foreground">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function MarketingPage() {
  const { data } = useProducts();
  const products = data?.products ?? [];
  const [product, setProduct] = useState("");
  const [type, setType] = useState(campaignTypes[0]!.key);
  const [details, setDetails] = useState("");
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState("");
  const [editing, setEditing] = useState(false);
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    if (!product) {
      toast.error("Pick a product first");
      return;
    }
    setLoading(true);
    setEditing(false);
    try {
      const res = await api.generateCampaign({ product, type, details });
      setContent(res.content);
    } catch {
      toast.error("Content generation failed", { description: "Please try again." });
    } finally {
      setLoading(false);
    }
  };

  const copy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    toast.success("Copied to clipboard");
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <Page title="Marketing" subtitle="Turn a product into ready-to-post promotion in three steps.">
      <div className="grid gap-6 lg:grid-cols-[1fr_1.1fr]">
        <Section title="Create a campaign" bodyClassName="p-0">
          <Step n={1} title="Select product">
            <Select value={product} onValueChange={setProduct}>
              <SelectTrigger className="h-10 w-full">
                <SelectValue placeholder="Choose a product" />
              </SelectTrigger>
              <SelectContent>
                {products.map((p) => (
                  <SelectItem key={p.product_id} value={p.name}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Step>

          <Step n={2} title="Choose campaign type">
            <div className="grid gap-2 sm:grid-cols-2">
              {campaignTypes.map((c) => (
                <button
                  key={c.key}
                  onClick={() => setType(c.key)}
                  className={cn(
                    "rounded-lg border p-3 text-left transition-all duration-200",
                    type === c.key
                      ? "border-primary bg-accent"
                      : "border-border hover:border-primary/30",
                  )}
                >
                  <p className="text-[13px] font-medium text-foreground">{c.key}</p>
                  <p className="mt-0.5 text-[12px] text-muted-foreground">{c.hint}</p>
                </button>
              ))}
            </div>
          </Step>

          <Step n={3} title="Add campaign details">
            <Textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              rows={4}
              placeholder="e.g. 15% off this weekend only, fresh stock just arrived"
            />
            <Button className="mt-4 w-full" onClick={generate} disabled={loading}>
              <Sparkles className="mr-1.5 size-4" />
              {loading ? "Generating…" : "Generate Content"}
            </Button>
          </Step>
        </Section>

        <Section
          title="Preview"
          description={content ? `${type} · ${product}` : "Your generated content appears here"}
          action={
            content && !loading ? (
              <div className="flex gap-1.5">
                <Button variant="outline" size="sm" onClick={copy}>
                  {copied ? <Check className="mr-1.5 size-3.5" /> : <Copy className="mr-1.5 size-3.5" />}
                  Copy
                </Button>
                <Button variant="outline" size="sm" onClick={generate}>
                  <RefreshCw className="mr-1.5 size-3.5" /> Regenerate
                </Button>
                <Button variant="outline" size="sm" onClick={() => setEditing((e) => !e)}>
                  <Pencil className="mr-1.5 size-3.5" /> {editing ? "Done" : "Edit"}
                </Button>
              </div>
            ) : null
          }
        >
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : !content ? (
            <EmptyState
              icon={<Sparkles className="size-6" />}
              title="Nothing generated yet"
              description="Pick a product and campaign type, then generate your content."
            />
          ) : editing ? (
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={12}
              className="text-[13.5px] leading-relaxed"
            />
          ) : (
            <div className="rounded-lg border border-border bg-muted/40 p-5">
              <p className="whitespace-pre-wrap text-[13.5px] leading-relaxed text-foreground">
                {content}
              </p>
            </div>
          )}
        </Section>
      </div>
    </Page>
  );
}
