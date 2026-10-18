import { useEffect, useState } from "react";
import { createFileRoute, Link, useNavigate, useRouter } from "@tanstack/react-router";
import {
  AlertCircle,
  Eye,
  EyeOff,
  Loader2,
  Lock,
  Mail,
  Store,
  User as UserIcon,
} from "lucide-react";
import { z } from "zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BizMateMark } from "@/components/layout/Sidebar";
import { useAuth } from "@/lib/auth-context";

const searchSchema = z.object({
  redirect: z.string().optional(),
});

export const Route = createFileRoute("/register")({
  validateSearch: searchSchema,
  component: RegisterPage,
  head: () => ({
    meta: [
      { title: "Create Account — BizMate" },
      {
        name: "description",
        content: "Register a new business account on BizMate.",
      },
    ],
  }),
});

function RegisterPage() {
  const { redirect } = Route.useSearch();
  const navigate = useNavigate();
  const router = useRouter();
  const { register, isAuthenticated, isLoading: isAuthLoading } = useAuth();

  const [name, setName] = useState("");
  const [storeName, setStoreName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [fieldErrors, setFieldErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // If already authenticated, redirect
  useEffect(() => {
    if (!isAuthLoading && isAuthenticated) {
      router.invalidate().then(() => {
        navigate({ to: redirect || "/" });
      });
    }
  }, [isAuthenticated, isAuthLoading, navigate, redirect, router]);

  const validate = (): boolean => {
    const errors: typeof fieldErrors = {};

    if (!name.trim()) {
      errors.name = "Full name is required.";
    } else if (name.trim().length < 2) {
      errors.name = "Name must be at least 2 characters.";
    }

    if (!email.trim()) {
      errors.email = "Email address is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      errors.email = "Please enter a valid email address.";
    }

    if (!password) {
      errors.password = "Password is required.";
    } else if (password.length < 6) {
      errors.password = "Password must be at least 6 characters.";
    }

    if (!confirmPassword) {
      errors.confirmPassword = "Please confirm your password.";
    } else if (password !== confirmPassword) {
      errors.confirmPassword = "Passwords do not match.";
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const newUser = await register({
        name: name.trim(),
        email: email.trim(),
        password,
        store_name: storeName.trim() || undefined,
      });

      toast.success(`Account created! Welcome to BizMate, ${newUser.name}.`);
      await router.invalidate();
      navigate({ to: redirect || "/" });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setServerError(err.message);
      } else {
        setServerError("Failed to create account. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 py-10 sm:px-6 lg:px-8">
      {/* Background ambient pattern */}
      <div className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center">
        <div className="h-[480px] w-[480px] rounded-full bg-primary/5 blur-3xl" />
      </div>

      <div className="w-full max-w-[460px] space-y-6">
        {/* Brand header */}
        <div className="flex flex-col items-center text-center">
          <div className="flex items-center gap-3">
            <BizMateMark className="size-11 rounded-xl text-base shadow-sm ring-4 ring-primary/10" />
            <div className="text-left">
              <span className="text-xl font-bold tracking-tight text-foreground">BizMate</span>
              <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Smart Retail Assistant
              </p>
            </div>
          </div>
          <h1 className="mt-5 text-2xl font-semibold tracking-tight text-foreground">
            Create your account
          </h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Set up your store dashboard to track inventory, sales, and insights
          </p>
        </div>

        {/* Register card */}
        <div className="panel overflow-hidden border border-border/70 bg-card p-7 shadow-raised">
          {serverError && (
            <div
              className="mb-5 flex items-start gap-3 rounded-lg border border-destructive/20 bg-destructive/10 p-3.5 text-[13px] text-destructive transition-all"
              role="alert"
            >
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <div className="leading-snug">{serverError}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div className="space-y-1.5">
              <Label
                htmlFor="reg-name"
                className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
              >
                Your Full Name
              </Label>
              <div className="relative">
                <UserIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/70" />
                <Input
                  id="reg-name"
                  type="text"
                  autoComplete="name"
                  placeholder="e.g. Sakshi Balte"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (fieldErrors.name) setFieldErrors((p) => ({ ...p, name: undefined }));
                  }}
                  className={`pl-9.5 ${fieldErrors.name ? "border-destructive focus-visible:ring-destructive" : ""}`}
                />
              </div>
              {fieldErrors.name && (
                <p className="text-[12px] text-destructive">{fieldErrors.name}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label
                htmlFor="reg-store"
                className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
              >
                Business / Store Name{" "}
                <span className="text-muted-foreground/60 font-normal normal-case">(optional)</span>
              </Label>
              <div className="relative">
                <Store className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/70" />
                <Input
                  id="reg-store"
                  type="text"
                  autoComplete="organization"
                  placeholder="e.g. Balte General Store"
                  value={storeName}
                  onChange={(e) => setStoreName(e.target.value)}
                  className="pl-9.5"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label
                htmlFor="reg-email"
                className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
              >
                Email Address
              </Label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/70" />
                <Input
                  id="reg-email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@yourbusiness.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: undefined }));
                  }}
                  className={`pl-9.5 ${fieldErrors.email ? "border-destructive focus-visible:ring-destructive" : ""}`}
                />
              </div>
              {fieldErrors.email && (
                <p className="text-[12px] text-destructive">{fieldErrors.email}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label
                htmlFor="reg-password"
                className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
              >
                Password{" "}
                <span className="text-muted-foreground/60 font-normal normal-case">
                  (min. 6 characters)
                </span>
              </Label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/70" />
                <Input
                  id="reg-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (fieldErrors.password)
                      setFieldErrors((p) => ({ ...p, password: undefined }));
                  }}
                  className={`pl-9.5 pr-10 ${fieldErrors.password ? "border-destructive focus-visible:ring-destructive" : ""}`}
                />
                <button
                  type="button"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground transition hover:text-foreground focus:outline-none"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
              {fieldErrors.password && (
                <p className="text-[12px] text-destructive">{fieldErrors.password}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label
                htmlFor="reg-confirm-password"
                className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
              >
                Confirm Password
              </Label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/70" />
                <Input
                  id="reg-confirm-password"
                  type={showConfirmPassword ? "text" : "password"}
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    if (fieldErrors.confirmPassword)
                      setFieldErrors((p) => ({ ...p, confirmPassword: undefined }));
                  }}
                  className={`pl-9.5 pr-10 ${
                    fieldErrors.confirmPassword
                      ? "border-destructive focus-visible:ring-destructive"
                      : ""
                  }`}
                />
                <button
                  type="button"
                  aria-label={
                    showConfirmPassword ? "Hide confirm password" : "Show confirm password"
                  }
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground transition hover:text-foreground focus:outline-none"
                >
                  {showConfirmPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
              {fieldErrors.confirmPassword && (
                <p className="text-[12px] text-destructive">{fieldErrors.confirmPassword}</p>
              )}
            </div>

            <Button type="submit" disabled={isSubmitting} className="mt-2 w-full font-medium">
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 size-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </Button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground font-medium">
                Already registered?
              </span>
            </div>
          </div>

          <div className="text-center">
            <Link
              to="/login"
              search={redirect ? { redirect } : undefined}
              className="inline-flex w-full items-center justify-center rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              Sign in to your account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
