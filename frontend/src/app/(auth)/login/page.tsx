"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Briefcase, User, Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";

import { authAPI } from "@/lib/api";
import { setToken, redirectByRole, type UserRole } from "@/lib/auth";

// ─── Validation schema ────────────────────────────────────────────────────────
const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

// ─── Role tabs ────────────────────────────────────────────────────────────────
type RoleTab = "candidate" | "hr";

const TABS: { id: RoleTab; label: string; icon: React.ReactNode }[] = [
  { id: "candidate", label: "Candidate", icon: <User className="w-4 h-4" /> },
  { id: "hr", label: "HR / Recruiter", icon: <Briefcase className="w-4 h-4" /> },
];

// ─── Component ────────────────────────────────────────────────────────────────
export default function LoginPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<RoleTab>("candidate");
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setIsLoading(true);
    setServerError(null);

    try {
      const { data } = await authAPI.login({
        email: values.email,
        password: values.password,
      });

      await setToken({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        role: data.role as UserRole,
        user_id: data.user_id,
        email: values.email,
      });

      toast.success("Logged in successfully!");
      redirectByRole(data.role as UserRole, router);
    } catch (err: unknown) {
      const status = (err as { response?: { status: number; data?: { detail?: string } } })
        ?.response?.status;
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Login failed. Please try again.";

      if (status === 401) {
        setServerError("Invalid email or password.");
      } else if (status === 403) {
        setServerError(
          typeof detail === "string"
            ? detail
            : "Account not verified or deactivated."
        );
      } else {
        setServerError(typeof detail === "string" ? detail : "Unexpected error.");
      }
      toast.error("Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-8">
      {/* Logo */}
      <div className="text-center mb-6">
        <span className="text-3xl font-bold text-brand-primary">DoneHR</span>
        <p className="text-slate-500 text-sm mt-1">AI-Powered HR Portal</p>
      </div>

      {/* Role tabs */}
      <div className="flex rounded-lg bg-slate-100 p-1 mb-6" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium
              transition-all duration-150
              ${
                activeTab === tab.id
                  ? "bg-white shadow-sm text-brand-primary"
                  : "text-slate-500 hover:text-slate-700"
              }
            `}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {/* Server error */}
        {serverError && (
          <div className="flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{serverError}</span>
          </div>
        )}

        {/* Email */}
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-slate-700 mb-1"
          >
            Email address
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            {...register("email")}
            className={`
              w-full rounded-lg border px-3 py-2.5 text-sm text-slate-900
              focus:outline-none focus:ring-2 focus:ring-brand-primary/40 focus:border-brand-primary
              transition-colors
              ${errors.email ? "border-red-400 bg-red-50" : "border-slate-300 bg-white"}
            `}
          />
          {errors.email && (
            <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
          )}
        </div>

        {/* Password */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label
              htmlFor="password"
              className="block text-sm font-medium text-slate-700"
            >
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-xs text-brand-primary hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            {...register("password")}
            className={`
              w-full rounded-lg border px-3 py-2.5 text-sm text-slate-900
              focus:outline-none focus:ring-2 focus:ring-brand-primary/40 focus:border-brand-primary
              transition-colors
              ${errors.password ? "border-red-400 bg-red-50" : "border-slate-300 bg-white"}
            `}
          />
          {errors.password && (
            <p className="mt-1 text-xs text-red-600">
              {errors.password.message}
            </p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isLoading}
          className="
            w-full flex items-center justify-center gap-2
            bg-brand-primary hover:bg-brand-primary-hover
            text-white font-semibold py-2.5 rounded-lg
            transition-colors disabled:opacity-60 disabled:cursor-not-allowed
          "
        >
          {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
          {isLoading ? "Signing in…" : "Sign In"}
        </button>
      </form>

      {/* Register link */}
      <p className="mt-6 text-center text-sm text-slate-500">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="text-brand-primary font-medium hover:underline"
        >
          Create one
        </Link>
      </p>
    </div>
  );
}
