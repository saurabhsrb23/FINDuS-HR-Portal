"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { User, Briefcase, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";

import { authAPI } from "@/lib/api";

// ─── Validation schema ────────────────────────────────────────────────────────
const PASSWORD_RULES = z
  .string()
  .min(8, "At least 8 characters")
  .regex(/[A-Z]/, "Must contain an uppercase letter")
  .regex(/[a-z]/, "Must contain a lowercase letter")
  .regex(/[0-9]/, "Must contain a digit")
  .regex(/[!@#$%^&*()_+\-=\[\]{}|;':",./<>?]/, "Must contain a special character");

const candidateSchema = z
  .object({
    full_name: z.string().min(1, "Full name is required").max(255),
    email: z.string().email("Enter a valid email"),
    password: PASSWORD_RULES,
    confirm_password: z.string(),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

const hrSchema = candidateSchema.innerType().extend({
  company_name: z.string().min(1, "Company name is required").max(255),
  confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});

type CandidateForm = z.infer<typeof candidateSchema>;
type HRForm = z.infer<typeof hrSchema>;
type RegisterForm = CandidateForm & { company_name?: string };

// ─── Component ────────────────────────────────────────────────────────────────
type RoleType = "candidate" | "hr";

const ROLE_CARDS: {
  id: RoleType;
  title: string;
  description: string;
  icon: React.ReactNode;
}[] = [
  {
    id: "candidate",
    title: "I'm a Candidate",
    description: "Browse jobs and apply",
    icon: <User className="w-6 h-6" />,
  },
  {
    id: "hr",
    title: "I'm in HR / Recruiting",
    description: "Post jobs and manage talent",
    icon: <Briefcase className="w-6 h-6" />,
  },
];

export default function RegisterPage() {
  const router = useRouter();
  const [selectedRole, setSelectedRole] = useState<RoleType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const schema = selectedRole === "hr" ? hrSchema : candidateSchema;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(schema as z.ZodType<RegisterForm>),
  });

  const onSubmit = async (values: RegisterForm) => {
    if (!selectedRole) return;
    setIsLoading(true);
    setServerError(null);

    try {
      await authAPI.register({
        email: values.email,
        password: values.password,
        confirm_password: values.confirm_password!,
        full_name: values.full_name,
        role: selectedRole === "hr" ? "hr" : "candidate",
        company_name: values.company_name,
      });

      setSuccess(true);
      toast.success("Account created! Check your email to verify.");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Registration failed. Please try again.";
      const status = (err as { response?: { status: number } })?.response?.status;

      if (status === 409) {
        setServerError("An account with this email already exists.");
      } else {
        setServerError(typeof detail === "string" ? detail : "Unexpected error.");
      }
      toast.error("Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  // ─── Success screen ──────────────────────────────────────────────────────
  if (success) {
    return (
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-8 text-center">
        <CheckCircle className="w-14 h-14 text-brand-accent mx-auto mb-4" />
        <h2 className="text-xl font-bold text-slate-800 mb-2">
          Check your inbox!
        </h2>
        <p className="text-slate-500 text-sm mb-6">
          We sent a verification link to your email. Click it to activate your
          account, then you can sign in.
        </p>
        <Link
          href="/login"
          className="inline-block bg-brand-primary text-white font-semibold px-6 py-2.5 rounded-lg hover:bg-brand-primary-hover transition-colors"
        >
          Go to Login
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <span className="text-3xl font-bold text-brand-primary">DoneHR</span>
        <p className="text-slate-500 text-sm mt-1">Create your account</p>
      </div>

      {/* Step 1 — Role selector */}
      {!selectedRole ? (
        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-600 mb-4 text-center">
            What brings you here?
          </p>
          {ROLE_CARDS.map((card) => (
            <button
              key={card.id}
              onClick={() => setSelectedRole(card.id)}
              className="
                w-full flex items-center gap-4 p-4 rounded-xl border-2 border-slate-200
                hover:border-brand-primary hover:bg-blue-50 transition-all text-left
              "
            >
              <span className="p-2 rounded-lg bg-brand-primary/10 text-brand-primary">
                {card.icon}
              </span>
              <div>
                <div className="font-semibold text-slate-800">{card.title}</div>
                <div className="text-xs text-slate-500">{card.description}</div>
              </div>
            </button>
          ))}
          <p className="text-center text-sm text-slate-500 mt-4">
            Already have an account?{" "}
            <Link href="/login" className="text-brand-primary font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      ) : (
        /* Step 2 — Registration form */
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          {/* Back button */}
          <button
            type="button"
            onClick={() => setSelectedRole(null)}
            className="text-xs text-slate-400 hover:text-slate-600 mb-2 flex items-center gap-1"
          >
            ← Change role
          </button>

          {/* Server error */}
          {serverError && (
            <div className="flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{serverError}</span>
            </div>
          )}

          {/* Full name */}
          <Field
            id="full_name"
            label="Full name"
            type="text"
            placeholder="Jane Smith"
            autoComplete="name"
            error={errors.full_name?.message}
            {...register("full_name")}
          />

          {/* Email */}
          <Field
            id="email"
            label="Email address"
            type="email"
            placeholder="jane@example.com"
            autoComplete="email"
            error={errors.email?.message}
            {...register("email")}
          />

          {/* Company (HR only) */}
          {selectedRole === "hr" && (
            <Field
              id="company_name"
              label="Company name"
              type="text"
              placeholder="Acme Corp"
              error={(errors as { company_name?: { message?: string } }).company_name?.message}
              {...register("company_name")}
            />
          )}

          {/* Password */}
          <Field
            id="password"
            label="Password"
            type="password"
            placeholder="••••••••"
            autoComplete="new-password"
            error={errors.password?.message}
            hint="Min 8 chars, uppercase, lowercase, digit, special character"
            {...register("password")}
          />

          {/* Confirm password */}
          <Field
            id="confirm_password"
            label="Confirm password"
            type="password"
            placeholder="••••••••"
            autoComplete="new-password"
            error={errors.confirm_password?.message}
            {...register("confirm_password")}
          />

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading}
            className="
              w-full flex items-center justify-center gap-2
              bg-brand-primary hover:bg-brand-primary-hover
              text-white font-semibold py-2.5 rounded-lg
              transition-colors disabled:opacity-60 disabled:cursor-not-allowed mt-2
            "
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            {isLoading ? "Creating account…" : "Create Account"}
          </button>

          <p className="text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="text-brand-primary font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      )}
    </div>
  );
}

// ─── Reusable form field ──────────────────────────────────────────────────────
import { forwardRef } from "react";

interface FieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  error?: string;
  hint?: string;
}

const Field = forwardRef<HTMLInputElement, FieldProps>(
  ({ id, label, error, hint, ...props }, ref) => (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-slate-700 mb-1">
        {label}
      </label>
      <input
        id={id}
        ref={ref}
        {...props}
        className={`
          w-full rounded-lg border px-3 py-2.5 text-sm text-slate-900
          focus:outline-none focus:ring-2 focus:ring-brand-primary/40 focus:border-brand-primary
          transition-colors
          ${error ? "border-red-400 bg-red-50" : "border-slate-300 bg-white"}
        `}
      />
      {hint && !error && (
        <p className="mt-1 text-xs text-slate-400">{hint}</p>
      )}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
);
Field.displayName = "Field";
