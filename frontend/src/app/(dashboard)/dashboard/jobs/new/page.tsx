"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createJob } from "@/lib/jobsAPI";
import type { JobCreate, JobType } from "@/types/job";
import { JOB_TYPE_LABELS } from "@/types/job";

const JOB_TYPES = Object.entries(JOB_TYPE_LABELS) as Array<[JobType, string]>;

export default function NewJobPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<JobCreate>({
    title: "",
    job_type: "full_time",
    currency: "USD",
  });

  function set<K extends keyof JobCreate>(key: K, value: JobCreate[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const job = await createJob(form);
      router.push(`/dashboard/jobs/${job.id}/edit`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to create job.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create Job Posting</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5 bg-white border border-gray-200 rounded-xl p-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Job Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            value={form.title}
            onChange={(e) => set("title", e.target.value)}
            placeholder="e.g. Senior Backend Engineer"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        {/* Job Type + Department */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Job Type
            </label>
            <select
              value={form.job_type}
              onChange={(e) => set("job_type", e.target.value as JobType)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              {JOB_TYPES.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Department
            </label>
            <input
              type="text"
              value={form.department ?? ""}
              onChange={(e) => set("department", e.target.value || undefined)}
              placeholder="e.g. Engineering"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
        </div>

        {/* Location */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Location
          </label>
          <input
            type="text"
            value={form.location ?? ""}
            onChange={(e) => set("location", e.target.value || undefined)}
            placeholder="e.g. San Francisco, CA"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        {/* Salary */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Salary Min
            </label>
            <input
              type="number"
              min={0}
              value={form.salary_min ?? ""}
              onChange={(e) =>
                set("salary_min", e.target.value ? Number(e.target.value) : undefined)
              }
              placeholder="60000"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Salary Max
            </label>
            <input
              type="number"
              min={0}
              value={form.salary_max ?? ""}
              onChange={(e) =>
                set("salary_max", e.target.value ? Number(e.target.value) : undefined)
              }
              placeholder="90000"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Currency
            </label>
            <input
              type="text"
              maxLength={3}
              value={form.currency}
              onChange={(e) => set("currency", e.target.value.toUpperCase())}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
        </div>

        {/* Experience */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Min Experience (years)
            </label>
            <input
              type="number"
              min={0}
              value={form.experience_years_min ?? ""}
              onChange={(e) =>
                set("experience_years_min", e.target.value ? Number(e.target.value) : undefined)
              }
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Experience (years)
            </label>
            <input
              type="number"
              min={0}
              value={form.experience_years_max ?? ""}
              onChange={(e) =>
                set("experience_years_max", e.target.value ? Number(e.target.value) : undefined)
              }
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
        </div>

        {/* Deadline */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Application Deadline
          </label>
          <input
            type="datetime-local"
            value={form.deadline ? form.deadline.slice(0, 16) : ""}
            onChange={(e) =>
              set("deadline", e.target.value ? new Date(e.target.value).toISOString() : undefined)
            }
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            rows={4}
            value={form.description ?? ""}
            onChange={(e) => set("description", e.target.value || undefined)}
            placeholder="Describe the role, team, and impact…"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
          />
        </div>

        {/* Requirements */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Requirements
          </label>
          <textarea
            rows={3}
            value={form.requirements ?? ""}
            onChange={(e) => set("requirements", e.target.value || undefined)}
            placeholder="List required qualifications, skills, experience…"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="px-5 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? "Creating…" : "Create as Draft"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="px-5 py-2 text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
