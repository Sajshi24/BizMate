import { useMemo, useRef, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Package,
  Search,
  ArrowUpDown,
  MoreHorizontal,
  PackageX,
  RefreshCw,
  Upload,
  X,
  FileText,
} from "lucide-react";
import { Page } from "@/components/layout/Page";
import { PrimaryAction } from "@/components/layout/PageHeader";
import { Section, EmptyState } from "@/components/ui/section";
import { StatusBadge } from "@/components/ui/status-badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProducts } from "@/hooks/useProducts";
import { importProductsCsv } from "@/services/api";
import { formatMoney, stockStatus } from "@/lib/format";
import { useQueryClient } from "@tanstack/react-query";
import { productsQueryOptions } from "@/hooks/useProducts";
import { toast } from "sonner";

export const Route = createFileRoute("/inventory")({
  component: InventoryPage,
  head: () => ({
    meta: [
      { title: "Inventory — BizMate" },
      {
        name: "description",
        content: "Monitor your products, suppliers and stock levels, and spot low stock early.",
      },
      { property: "og:title", content: "Inventory — BizMate" },
      {
        property: "og:description",
        content: "Monitor your products and keep your stock healthy.",
      },
      { property: "og:url", content: "/inventory" },
    ],
    links: [{ rel: "canonical", href: "/inventory" }],
  }),
});

type SortKey = "name" | "stock" | "selling_price";

function CsvUploadDialog({
  open,
  onClose,
  onSuccess,
}: {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
    setError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a CSV file first.");
      return;
    }
    setIsUploading(true);
    setError(null);
    try {
      const result = await importProductsCsv(selectedFile);
      toast.success(result.message);
      onSuccess();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/40 px-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b border-border p-5">
          <div>
            <h2 className="text-[15px] font-semibold text-foreground">Upload CSV</h2>
            <p className="mt-0.5 text-[12px] text-muted-foreground">
              Import products from a CSV file into your account
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Close"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
            className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-border py-8 px-4 text-center transition-colors hover:border-primary/50 hover:bg-muted/30"
          >
            <Upload className="size-8 text-muted-foreground mb-3" strokeWidth={1.5} />
            {selectedFile ? (
              <div className="flex items-center gap-2 text-sm text-foreground">
                <FileText className="size-4 text-primary" />
                <span className="font-medium">{selectedFile.name}</span>
              </div>
            ) : (
              <>
                <p className="text-[13px] font-medium text-foreground">
                  Click to select or drag & drop
                </p>
                <p className="text-[12px] text-muted-foreground mt-1">CSV files only</p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileChange}
          />

          {/* CSV format hint */}
          <div className="rounded-lg border border-border bg-muted/30 p-3">
            <p className="text-[11.5px] font-medium uppercase tracking-wide text-muted-foreground mb-1.5">
              Required columns
            </p>
            <p className="text-[12px] text-muted-foreground font-mono leading-relaxed">
              name, category, cost_price, selling_price, stock, minimum_stock, supplier
            </p>
          </div>

          {error && (
            <div className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-[13px] text-destructive">
              {error}
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <Button variant="outline" className="flex-1" onClick={onClose} disabled={isUploading}>
              Cancel
            </Button>
            <Button
              className="flex-1"
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
            >
              {isUploading ? "Importing…" : "Import Products"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function InventoryPage() {
  const { data, isLoading, isError, refetch, isFetching } = useProducts();
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState<SortKey>("name");
  const [csvOpen, setCsvOpen] = useState(false);

  const products = data?.products ?? [];
  const categories = useMemo(
    () => Array.from(new Set(products.map((p) => p.category))).sort(),
    [products],
  );

  const rows = useMemo(() => {
    return products
      .filter(
        (p) =>
          (category === "all" || p.category === category) &&
          (p.name.toLowerCase().includes(q.toLowerCase()) ||
            p.supplier.toLowerCase().includes(q.toLowerCase())),
      )
      .sort((a, b) =>
        sort === "name" ? a.name.localeCompare(b.name) : Number(b[sort]) - Number(a[sort]),
      );
  }, [products, q, category, sort]);

  const counts = {
    total: products.length,
    healthy: products.filter((p) => stockStatus(p) === "healthy").length,
    low: products.filter((p) => stockStatus(p) === "low").length,
    critical: products.filter((p) => stockStatus(p) === "critical").length,
  };

  const handleCsvSuccess = () => {
    // Invalidate the products query so the list refreshes automatically
    void queryClient.invalidateQueries({ queryKey: productsQueryOptions.queryKey });
  };

  return (
    <>
      <CsvUploadDialog
        open={csvOpen}
        onClose={() => setCsvOpen(false)}
        onSuccess={handleCsvSuccess}
      />

      <Page
        title="Inventory"
        subtitle="Monitor your products and keep your stock healthy."
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5"
              onClick={() => setCsvOpen(true)}
            >
              <Upload className="size-4" />
              Upload CSV
            </Button>
            <PrimaryAction
              onClick={() =>
                toast("Add product", {
                  description: "Product intake opens once your catalogue service is connected.",
                })
              }
            >
              Add Product
            </PrimaryAction>
          </div>
        }
      >
        <div className="panel grid grid-cols-2 divide-border sm:grid-cols-4 sm:divide-x">
          {[
            { label: "Total Products", value: counts.total },
            { label: "Healthy Stock", value: counts.healthy },
            { label: "Low Stock", value: counts.low },
            { label: "Critical Stock", value: counts.critical },
          ].map((s) => (
            <div key={s.label} className="p-5">
              <p className="text-[12px] font-medium uppercase tracking-wide text-muted-foreground">
                {s.label}
              </p>
              <p className="num mt-2 text-[24px] font-semibold leading-none text-foreground">
                {isLoading ? "—" : s.value}
              </p>
            </div>
          ))}
        </div>

        <Section
          className="mt-6"
          bodyClassName="p-0"
          title="Products"
          description={`${rows.length} of ${products.length} products`}
          action={
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search products"
                  className="h-9 w-full pl-8 sm:w-56"
                />
              </div>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="h-9 w-[150px]">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All categories</SelectItem>
                  {categories.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={sort} onValueChange={(v) => setSort(v as SortKey)}>
                <SelectTrigger className="h-9 w-[150px]">
                  <ArrowUpDown className="size-3.5 text-muted-foreground" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">Name A–Z</SelectItem>
                  <SelectItem value="stock">Highest stock</SelectItem>
                  <SelectItem value="selling_price">Highest price</SelectItem>
                </SelectContent>
              </Select>
            </div>
          }
        >
          {isLoading ? (
            <div className="space-y-2 p-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full rounded-lg" />
              ))}
            </div>
          ) : isError ? (
            <div className="p-5">
              <EmptyState
                icon={<PackageX className="size-6" />}
                title="We couldn't load your products"
                description="The business service didn't respond. Check that it's running and try again."
                action={
                  <Button variant="outline" size="sm" onClick={() => refetch()}>
                    <RefreshCw className="mr-1.5 size-3.5" /> Try again
                  </Button>
                }
              />
            </div>
          ) : rows.length === 0 ? (
            <div className="p-5">
              {products.length === 0 ? (
                <EmptyState
                  icon={<Package className="size-6" />}
                  title="No products yet"
                  description="Upload a CSV file to import your products, or add them one by one."
                  action={
                    <Button variant="outline" size="sm" onClick={() => setCsvOpen(true)}>
                      <Upload className="mr-1.5 size-3.5" /> Upload CSV
                    </Button>
                  }
                />
              ) : (
                <EmptyState
                  icon={<Package className="size-6" />}
                  title="No products match your filters"
                  description="Try a different search term or clear the category filter."
                  action={
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setQ("");
                        setCategory("all");
                      }}
                    >
                      Clear filters
                    </Button>
                  }
                />
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left">
                <thead>
                  <tr className="border-b border-border text-[11.5px] uppercase tracking-wide text-muted-foreground">
                    <th className="px-5 py-3 font-medium">Product</th>
                    <th className="px-5 py-3 font-medium">Category</th>
                    <th className="px-5 py-3 text-right font-medium">Cost</th>
                    <th className="px-5 py-3 text-right font-medium">Selling</th>
                    <th className="px-5 py-3 text-right font-medium">Stock</th>
                    <th className="px-5 py-3 font-medium">Supplier</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {rows.map((p) => (
                    <tr
                      key={p.product_id}
                      className="border-b border-border/70 transition-colors last:border-0 hover:bg-muted/50"
                    >
                      <td className="px-5 py-3.5">
                        <p className="text-[13.5px] font-medium text-foreground">{p.name}</p>
                        <p className="text-[12px] text-muted-foreground">
                          Min. {p.minimum_stock} units
                        </p>
                      </td>
                      <td className="px-5 py-3.5 text-[13px] text-muted-foreground">
                        {p.category}
                      </td>
                      <td className="num px-5 py-3.5 text-right text-[13px] text-muted-foreground">
                        {formatMoney(p.cost_price)}
                      </td>
                      <td className="num px-5 py-3.5 text-right text-[13px] font-medium text-foreground">
                        {formatMoney(p.selling_price)}
                      </td>
                      <td className="num px-5 py-3.5 text-right text-[13px] text-foreground">
                        {p.stock}
                      </td>
                      <td className="px-5 py-3.5 text-[13px] text-muted-foreground">
                        {p.supplier}
                      </td>
                      <td className="px-5 py-3.5">
                        <StatusBadge status={stockStatus(p)} />
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          onClick={() =>
                            toast(p.name, {
                              description: "Product editing arrives with the next release.",
                            })
                          }
                          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                          aria-label={`Actions for ${p.name}`}
                        >
                          <MoreHorizontal className="size-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {isFetching && !isLoading && (
            <p className="border-t border-border px-5 py-2 text-[12px] text-muted-foreground">
              Refreshing…
            </p>
          )}
        </Section>
      </Page>
    </>
  );
}
