import type { ReactNode } from "react";
import { Bell, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";

export function PageHeader({
  title,
  subtitle,
  action,
  onOpenNav,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  onOpenNav?: () => void;
}) {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur">
      <div className="flex min-h-16 flex-wrap items-center gap-3 px-4 py-3 sm:px-6 lg:px-8">
        <button
          onClick={onOpenNav}
          className="-ml-1 rounded-md p-2 text-muted-foreground hover:bg-muted lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="size-5" />
        </button>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-[17px] font-semibold text-foreground">{title}</h1>
          {subtitle && <p className="truncate text-[13px] text-muted-foreground">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-2">
          <button
            className="relative rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Notifications"
          >
            <Bell className="size-[18px]" strokeWidth={1.8} />
            <span className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-destructive" />
          </button>
          <span className="hidden size-8 items-center justify-center rounded-full bg-accent text-[12px] font-semibold text-accent-foreground sm:flex">
            SB
          </span>
          {action}
        </div>
      </div>
    </header>
  );
}

export function PrimaryAction({
  children,
  onClick,
}: {
  children: ReactNode;
  onClick?: () => void;
}) {
  return (
    <Button size="sm" className="h-9" onClick={onClick}>
      {children}
    </Button>
  );
}
