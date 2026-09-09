import type { ReactNode } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { useNav } from "@/routes/__root";
import { cn } from "@/lib/utils";

export function Page({
  title,
  subtitle,
  action,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const { openNav } = useNav();
  return (
    <>
      <PageHeader title={title} subtitle={subtitle} action={action} onOpenNav={openNav} />
      <main className={cn("mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6 lg:px-8", className)}>
        {children}
      </main>
    </>
  );
}
