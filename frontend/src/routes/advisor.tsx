import { useEffect, useRef, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Send, Sparkles } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useProducts } from "@/hooks/useProducts";
import { api } from "@/services/api";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/advisor")({
  component: AdvisorPage,
  head: () => ({
    meta: [
      { title: "AI Advisor — BizMate" },
      {
        name: "description",
        content: "Ask BizMate AI about your business and get clear, actionable answers.",
      },
      { property: "og:title", content: "AI Advisor — BizMate" },
      { property: "og:description", content: "Your intelligent business advisor, always on hand." },
      { property: "og:url", content: "/advisor" },
    ],
    links: [{ rel: "canonical", href: "/advisor" }],
  }),
});

const suggestions = [
  "Which products need my attention?",
  "How are my sales performing?",
  "What should I restock?",
  "Give me a summary of my business.",
];

interface Msg {
  role: "user" | "ai";
  text: string;
}

function AdvisorPage() {
  const { data } = useProducts();
  const products = data?.products ?? [];
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const ask = async (question: string) => {
    if (!question.trim() || thinking) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setThinking(true);
    const answer = await api.askAdvisor(question, products);
    setMessages((m) => [...m, { role: "ai", text: answer }]);
    setThinking(false);
  };

  return (
    <Page title="AI Advisor" subtitle="Ask BizMate AI anything about your business.">
      <div className="panel flex h-[calc(100vh-11rem)] flex-col">
        <div className="flex-1 overflow-y-auto p-5">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <span className="flex size-11 items-center justify-center rounded-xl bg-accent text-accent-foreground">
                <Sparkles className="size-5" strokeWidth={1.8} />
              </span>
              <h2 className="mt-4 text-[18px] font-semibold tracking-tight text-foreground">
                Your intelligent business advisor
              </h2>
              <p className="mt-1.5 max-w-sm text-[13.5px] text-muted-foreground">
                Ask questions about your business and get actionable insights.
              </p>
              <div className="mt-6 grid w-full max-w-lg gap-2 sm:grid-cols-2">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => ask(s)}
                    className="rounded-lg border border-border p-3 text-left text-[13px] text-foreground transition-all duration-200 hover:border-primary/30 hover:shadow-[var(--shadow-raised)]"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-2xl space-y-4">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={cn("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}
                >
                  {m.role === "ai" && (
                    <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                      <Sparkles className="size-3.5" strokeWidth={1.9} />
                    </span>
                  )}
                  <div
                    className={cn(
                      "max-w-[85%] rounded-xl px-4 py-2.5 text-[13.5px] leading-relaxed",
                      m.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "border border-border bg-muted/50 text-foreground",
                    )}
                  >
                    {m.text}
                  </div>
                </div>
              ))}
              {thinking && (
                <div className="flex gap-3">
                  <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                    <Sparkles className="size-3.5" strokeWidth={1.9} />
                  </span>
                  <div className="flex items-center gap-1.5 rounded-xl border border-border bg-muted/50 px-4 py-3.5">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="size-1.5 animate-bounce rounded-full bg-muted-foreground"
                        style={{ animationDelay: `${i * 0.12}s` }}
                      />
                    ))}
                  </div>
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <div className="border-t border-border p-4">
          <form
            className="mx-auto flex max-w-2xl gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about sales, stock, profit…"
              className="h-10"
            />
            <Button type="submit" className="h-10 px-3.5" disabled={thinking || !input.trim()}>
              <Send className="size-4" />
              <span className="sr-only">Send</span>
            </Button>
          </form>
        </div>
      </div>
    </Page>
  );
}
