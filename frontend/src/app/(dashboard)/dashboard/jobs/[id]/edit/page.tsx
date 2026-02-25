"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  addSkill,
  closeJob,
  getJob,
  pauseJob,
  publishJob,
  removeSkill,
  updateJob,
} from "@/lib/jobsAPI";
import type { Job, JobType, JobUpdate } from "@/types/job";
import { JOB_STATUS_COLORS, JOB_STATUS_LABELS, JOB_TYPE_LABELS } from "@/types/job";

const JOB_TYPES = Object.entries(JOB_TYPE_LABELS) as Array<[JobType, string]>;

export default function EditJobPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newSkill, setNewSkill] = useState("");

  const [form, setForm] = useState<JobUpdate>({});

  useEffect(() => {
    getJob(id)
      .then((j) => {
        setJob(j);
        setForm({
          title: j.title,
          description: j.description ?? undefined,
          requirements: j.requirements ?? undefined,
          location: j.location ?? undefined,
          job_type: j.job_type,
          department: j.department ?? undefined,
          salary_min: j.salary_min ?? undefined,
          salary_max: j.salary_max ?? undefined,
          currency: j.currency,
          experience_years_min: j.experience_years_min ?? undefined,
          experience_years_max: j.experience_years_max ?? undefined,
          deadline: j.deadline ?? undefined,
        });
      })
      .catch(() => setError("Failed to load job."))
      .finally(() => setLoading(false));
  }, [id]);

  function set<K extends keyof JobUpdate>(key: K, value: JobUpdate[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateJob(id, form);
      setJob(updated);
    } catch {
      setError("Failed to save changes.");
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish() {
    const updated = await publishJob(id);
    setJob(updated);
  }

  async function handlePause() {
    const updated = await pauseJob(id);
    setJob(updated);
  }

  async function handleClose() {
    const updated = await closeJob(id);
    setJob(updated);
  }

  async function handleAddSkill() {
    if (!newSkill.trim()) return;
    const skill = await addSkill(id, { skill_name: newSkill.trim() });
    setJob((prev) => prev && { ...prev, skills: [...prev.skills, skill] });
    setNewSkill("");
  }

  async function handleRemoveSkill(skillId: string) {
    await removeSkill(id, skillId);
    setJob((prev) =>
      prev && { ...prev, skills: prev.skills.filter((s) => s.id !== skillId) }
    );
  }

  if (loading) return <div className="p-8 text-gray-500">Loading…</div>;
  if (error || !job)
    return <div className="p-8 text-red-600">{error ?? "Job not found"}</div>;

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Edit Job</h1>
          <span
            className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full font-medium ${
              JOB_STATUS_COLORS[job.status]
            }`}
          >
            {JOB_STATUS_LABELS[job.status]}
          </span>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {job.status === "draft" && (
            <button
              onClick={handlePublish}
              className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
            >
              Publish
            </button>
          )}
          {job.status === "active" && (
            <button
              onClick={handlePause}
              className="px-3 py-1.5 text-sm bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 font-medium"
            >
              Pause
            </button>
          )}
          {(job.status === "active" || job.status === "paused") && (
            <button
              onClick={handleClose}
              className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
            >
              Close
            </button>
          )}
          <button
            onClick={() => router.push(`/dashboard/jobs/${id}/pipeline`)}
            className="px-3 py-1.5 text-sm bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 font-medium"
          >
            Pipeline
          </button>
          <button
            onClick={() => router.push(`/dashboard/jobs/${id}/questionnaire`)}
            className="px-3 py-1.5 text-sm bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 font-medium"
          >
            Questions
          </button>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSave} className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Job Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            value={form.title ?? ""}
            onChange={(e) => set("title", e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Job Type</label>
            <select
              value={form.job_type ?? "full_time"}
              onChange={(e) => set("job_type", e.target.value as JobType)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              {JOB_TYPES.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
            <input
              type="text"
              value={form.department ?? ""}
              onChange={(e) => set("department", e.target.value || undefined)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
          <input
            type="text"
            value={form.location ?? ""}
            onChange={(e) => set("location", e.target.value || undefined)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Salary Min</label>
            <input
              type="number" min={0}
              value={form.salary_min ?? ""}
              onChange={(e) => set("salary_min", e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Salary Max</label>
            <input
              type="number" min={0}
              value={form.salary_max ?? ""}
              onChange={(e) => set("salary_max", e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
            <input
              type="text" maxLength={3}
              value={form.currency ?? "USD"}
              onChange={(e) => set("currency", e.target.value.toUpperCase())}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Experience (yrs)</label>
            <input
              type="number" min={0}
              value={form.experience_years_min ?? ""}
              onChange={(e) => set("experience_years_min", e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Experience (yrs)</label>
            <input
              type="number" min={0}
              value={form.experience_years_max ?? ""}
              onChange={(e) => set("experience_years_max", e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Application Deadline</label>
          <input
            type="datetime-local"
            value={form.deadline ? form.deadline.slice(0, 16) : ""}
            onChange={(e) => set("deadline", e.target.value ? new Date(e.target.value).toISOString() : undefined)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            rows={4}
            value={form.description ?? ""}
            onChange={(e) => set("description", e.target.value || undefined)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Requirements</label>
          <textarea
            rows={3}
            value={form.requirements ?? ""}
            onChange={(e) => set("requirements", e.target.value || undefined)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
          />
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save Changes"}
          </button>
          <button type="button" onClick={() => router.back()} className="px-5 py-2 text-sm text-gray-600 hover:text-gray-900">
            Cancel
          </button>
        </div>
      </form>

      {/* Skills */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Required Skills</h2>
        <div className="flex flex-wrap gap-2 mb-4">
          {job.skills.map((s) => (
            <span
              key={s.id}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-sm"
            >
              {s.skill_name}
              <button
                onClick={() => handleRemoveSkill(s.id)}
                className="text-indigo-400 hover:text-indigo-700 leading-none"
              >
                ×
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newSkill}
            onChange={(e) => setNewSkill(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddSkill())}
            placeholder="Add skill (press Enter)"
            className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
          <button
            onClick={handleAddSkill}
            className="px-3 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
          >
            Add
          </button>
        </div>
      </div>
    </div>
  );
}
