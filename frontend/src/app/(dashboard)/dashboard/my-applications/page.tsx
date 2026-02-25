"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MapPin, Calendar, ChevronDown, ChevronUp, Trash2, AlertCircle } from "lucide-react";
import { toast } from "sonner";

import { applicationAPI } from "@/lib/applicationAPI";
import type { Application, ApplicationListItem, ApplicationStatus, TimelineEvent } from "@/types/application";

const STATUS_CONFIG: Record<ApplicationStatus, { label: string; color: string; dot: string }> = {
  applied:    { label: "Applied",    color: "bg-blue-100 text-blue-700 border-blue-200",       dot: "bg-blue-500" },
  screening:  { label: "Screening",  color: "bg-amber-100 text-amber-700 border-amber-200",    dot: "bg-amber-500" },
  interview:  { label: "Interview",  color: "bg-purple-100 text-purple-700 border-purple-200", dot: "bg-purple-500" },
  offer:      { label: "Offer",      color: "bg-green-100 text-green-700 border-green-200",    dot: "bg-green-500" },
  hired:      { label: "Hired",      color: "bg-green-100 text-green-800 border-green-300",    dot: "bg-green-600" },
  rejected:   { label: "Rejected",   color: "bg-red-100 text-red-700 border-red-200",          dot: "bg-red-500" },
  withdrawn:  { label: "Withdrawn",  color: "bg-gray-100 text-gray-600 border-gray-200",       dot: "bg-gray-400" },
};

function Timeline({ events }: { events: TimelineEvent[] }) {
  return (
    <div className="mt-4 pl-2">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Application Timeline</p>
      <div className="relative">
        <div className="absolute left-2 top-0 bottom-0 w-0.5 bg-gray-200" />
        <div className="space-y-4 pl-7">
          {events.map((e, i) => {
            const cfg = STATUS_CONFIG[e.status] || STATUS_CONFIG.applied;
            return (
              <div key={i} className="relative">
                <div className={`absolute -left-5 w-3 h-3 rounded-full border-2 border-white ${cfg.dot}`} />
                <div>
                  <p className="text-sm font-medium text-gray-800 capitalize">{e.status}</p>
                  {e.note && <p className="text-xs text-gray-500">{e.note}</p>}
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(e.timestamp).toLocaleString("en-IN", {
                      day: "numeric", month: "short", year: "numeric",
                      hour: "2-digit", minute: "2-digit"
                    })}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function AppCard({ item, onWithdraw }: {
  item: ApplicationListItem;
  onWithdraw: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<Application | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const cfg = STATUS_CONFIG[item.status] || STATUS_CONFIG.applied;

  const toggleExpand = async () => {
    if (!expanded && !detail) {
      setLoadingDetail(true);
      try {
        const r = await applicationAPI.getApplicationDetail(item.id);
        setDetail(r.data);
      } catch { toast.error("Failed to load details"); }
      finally { setLoadingDetail(false); }
    }
    setExpanded(e => !e);
  };

  const canWithdraw = !["hired", "rejected", "withdrawn"].includes(item.status);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">{item.job_title || "Unknown Role"}</h3>
            <p className="text-sm text-gray-600 mt-0.5">{item.company_name || "Company"}</p>
          </div>
          <span className={`shrink-0 text-xs border px-2.5 py-1 rounded-full font-medium ${cfg.color}`}>
            {cfg.label}
          </span>
        </div>

        <div className="flex flex-wrap gap-3 mt-3 text-xs text-gray-500">
          {item.job_location && (
            <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {item.job_location}</span>
          )}
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            Applied {new Date(item.applied_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
          </span>
        </div>

        <div className="flex items-center gap-2 mt-4">
          <button
            onClick={toggleExpand}
            className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            {loadingDetail ? "Loading…" : expanded ? "Hide timeline" : "View timeline"}
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {canWithdraw && (
            <button
              onClick={() => onWithdraw(item.id)}
              className="ml-auto flex items-center gap-1 text-xs text-red-500 hover:text-red-700 transition-colors"
            >
              <Trash2 className="w-3 h-3" /> Withdraw
            </button>
          )}
        </div>
      </div>

      {expanded && detail?.timeline && (
        <div className="border-t border-gray-100 px-5 pb-5">
          <Timeline events={detail.timeline} />
        </div>
      )}
    </div>
  );
}

export default function MyApplicationsPage() {
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [withdrawing, setWithdrawing] = useState<string | null>(null);

  const load = async () => {
    try {
      const r = await applicationAPI.getMyApplications();
      setApplications(r.data);
    } catch {
      toast.error("Failed to load applications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleWithdraw = async (id: string) => {
    if (!confirm("Are you sure you want to withdraw this application?")) return;
    setWithdrawing(id);
    try {
      await applicationAPI.withdraw(id);
      toast.success("Application withdrawn");
      load();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || "Failed to withdraw");
    } finally {
      setWithdrawing(null);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
    </div>
  );

  const active = applications.filter(a => !["hired", "rejected", "withdrawn"].includes(a.status));
  const closed = applications.filter(a => ["hired", "rejected", "withdrawn"].includes(a.status));

  return (
    <div className="max-w-3xl pb-12">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Applications</h1>
        <p className="text-sm text-gray-500 mt-1">
          {applications.length} total · {active.length} active
        </p>
      </div>

      {applications.length === 0 ? (
        <div className="text-center py-20 text-gray-400 bg-white rounded-xl border border-gray-200">
          <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium">No applications yet</p>
          <p className="text-sm mt-1">Start applying to jobs to track them here</p>
          <Link
            href="/dashboard/browse-jobs"
            className="mt-4 inline-block bg-indigo-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700"
          >
            Browse Jobs
          </Link>
        </div>
      ) : (
        <>
          {active.length > 0 && (
            <div className="space-y-4 mb-8">
              <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Active ({active.length})</h2>
              {active.map(app => (
                <AppCard key={app.id} item={app} onWithdraw={handleWithdraw} />
              ))}
            </div>
          )}
          {closed.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Closed ({closed.length})</h2>
              {closed.map(app => (
                <AppCard key={app.id} item={app} onWithdraw={handleWithdraw} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
