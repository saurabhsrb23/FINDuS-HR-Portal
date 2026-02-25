"use client";

import { useEffect, useState } from "react";
import { Bell, Plus, Trash2, BellOff } from "lucide-react";
import { toast } from "sonner";

import { applicationAPI } from "@/lib/applicationAPI";
import type { JobAlert } from "@/types/application";

export default function JobAlertsPage() {
  const [alerts, setAlerts] = useState<JobAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: "", keywords: "", location: "",
    job_type: "", salary_min: "",
  });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const r = await applicationAPI.getAlerts();
      setAlerts(r.data);
    } catch {
      toast.error("Failed to load alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const createAlert = async () => {
    if (!form.title.trim()) { toast.error("Alert title is required"); return; }
    setSaving(true);
    try {
      await applicationAPI.createAlert({
        title: form.title,
        keywords: form.keywords || undefined,
        location: form.location || undefined,
        job_type: form.job_type || undefined,
        salary_min: form.salary_min ? Number(form.salary_min) : undefined,
      });
      toast.success("Job alert created! You'll receive a daily digest.");
      setForm({ title: "", keywords: "", location: "", job_type: "", salary_min: "" });
      setShowForm(false);
      load();
    } catch {
      toast.error("Failed to create alert");
    } finally {
      setSaving(false);
    }
  };

  const deleteAlert = async (id: string) => {
    try {
      await applicationAPI.deleteAlert(id);
      toast.success("Alert deleted");
      load();
    } catch {
      toast.error("Failed to delete alert");
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
    </div>
  );

  return (
    <div className="max-w-2xl pb-12">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Alerts</h1>
          <p className="text-sm text-gray-500 mt-1">
            Get a daily email digest of matching jobs at 7:00 AM
          </p>
        </div>
        <button
          onClick={() => setShowForm(s => !s)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> New Alert
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-5 space-y-4">
          <h3 className="font-semibold text-gray-900">Create Job Alert</h3>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Alert Name *</label>
            <input
              value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              placeholder="e.g. Senior React Developer"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Keywords (comma-separated)</label>
              <input
                value={form.keywords}
                onChange={e => setForm(f => ({ ...f, keywords: e.target.value }))}
                placeholder="react, typescript, node"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Location</label>
              <input
                value={form.location}
                onChange={e => setForm(f => ({ ...f, location: e.target.value }))}
                placeholder="Bangalore, Remote..."
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Job Type</label>
              <select
                value={form.job_type}
                onChange={e => setForm(f => ({ ...f, job_type: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none"
              >
                <option value="">Any</option>
                <option value="full_time">Full Time</option>
                <option value="part_time">Part Time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Min Salary (INR)</label>
              <input
                type="number"
                value={form.salary_min}
                onChange={e => setForm(f => ({ ...f, salary_min: e.target.value }))}
                placeholder="600000"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={createAlert}
              disabled={saving}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-60"
            >
              {saving ? "Creating…" : "Create Alert"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="border border-gray-200 text-gray-600 px-5 py-2 rounded-lg text-sm hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Alert list */}
      {alerts.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border border-gray-200 text-gray-400">
          <BellOff className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium">No alerts yet</p>
          <p className="text-sm mt-1">Create an alert to get notified about matching jobs daily</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map(alert => (
            <div key={alert.id} className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 bg-indigo-50 rounded-lg flex items-center justify-center shrink-0">
                  <Bell className="w-4 h-4 text-indigo-600" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{alert.title}</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {alert.keywords && (
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                        {alert.keywords}
                      </span>
                    )}
                    {alert.location && (
                      <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                        {alert.location}
                      </span>
                    )}
                    {alert.job_type && (
                      <span className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full capitalize">
                        {alert.job_type.replace("_", " ")}
                      </span>
                    )}
                    {alert.salary_min && (
                      <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">
                        ₹{(alert.salary_min / 100000).toFixed(1)}L+
                      </span>
                    )}
                  </div>
                  {alert.last_sent_at && (
                    <p className="text-xs text-gray-400 mt-1.5">
                      Last sent: {new Date(alert.last_sent_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => deleteAlert(alert.id)}
                className="shrink-0 text-red-400 hover:text-red-600 p-1 transition-colors"
                title="Delete alert"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
