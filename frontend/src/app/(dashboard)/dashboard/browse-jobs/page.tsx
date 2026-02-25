"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, MapPin, Briefcase, IndianRupee, Clock, ArrowRight } from "lucide-react";
import { toast } from "sonner";

import { applicationAPI } from "@/lib/applicationAPI";
import type { JobSearchResult } from "@/types/application";

const JOB_TYPES = [
  { value: "", label: "All Types" },
  { value: "full_time", label: "Full Time" },
  { value: "part_time", label: "Part Time" },
  { value: "contract", label: "Contract" },
  { value: "internship", label: "Internship" },
  { value: "remote", label: "Remote" },
];

function fmt(n: number) {
  return n >= 100000
    ? `₹${(n / 100000).toFixed(1)}L`
    : `₹${(n / 1000).toFixed(0)}K`;
}

function JobCard({ job, onApply }: { job: JobSearchResult; onApply: (id: string) => void }) {
  const daysAgo = Math.floor(
    (Date.now() - new Date(job.created_at).getTime()) / 86400000
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{job.title}</h3>
          <p className="text-sm text-gray-600 mt-0.5">{job.company_name || "Company"}</p>
        </div>
        <span className="shrink-0 text-xs bg-green-100 text-green-700 border border-green-200 px-2 py-0.5 rounded-full font-medium">
          Active
        </span>
      </div>

      <div className="flex flex-wrap gap-3 text-xs text-gray-500">
        {job.location && (
          <span className="flex items-center gap-1">
            <MapPin className="w-3 h-3" /> {job.location}
          </span>
        )}
        {job.job_type && (
          <span className="flex items-center gap-1 capitalize">
            <Briefcase className="w-3 h-3" /> {job.job_type.replace("_", " ")}
          </span>
        )}
        {(job.salary_min || job.salary_max) && (
          <span className="flex items-center gap-1">
            <IndianRupee className="w-3 h-3" />
            {job.salary_min ? fmt(job.salary_min) : "?"}
            {job.salary_max ? ` – ${fmt(job.salary_max)}` : "+"}
          </span>
        )}
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {daysAgo === 0 ? "Today" : `${daysAgo}d ago`}
        </span>
      </div>

      {job.skills && job.skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {job.skills.slice(0, 5).map((s) => (
            <span
              key={s.skill_name}
              className={`text-xs px-2 py-0.5 rounded-full border ${
                s.is_required
                  ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                  : "bg-gray-50 text-gray-600 border-gray-200"
              }`}
            >
              {s.skill_name}
            </span>
          ))}
        </div>
      )}

      <button
        onClick={() => onApply(job.id)}
        className="mt-auto flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-lg text-sm font-medium transition-colors"
      >
        Apply Now <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}

export default function BrowseJobsPage() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [location, setLocation] = useState("");
  const [jobType, setJobType] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<{
    items: JobSearchResult[]; total: number; pages: number;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const search = async (resetPage = false) => {
    const p = resetPage ? 1 : page;
    if (resetPage) setPage(1);
    setLoading(true);
    try {
      const res = await applicationAPI.searchJobs({
        q: q || undefined,
        location: location || undefined,
        job_type: jobType || undefined,
        page: p,
        limit: 12,
      });
      setData(res.data);
    } catch {
      toast.error("Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { search(); }, [page]);

  const handleApply = (jobId: string) => {
    router.push(`/dashboard/browse-jobs/${jobId}/apply`);
  };

  return (
    <div className="max-w-5xl pb-12">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Browse Jobs</h1>
        <p className="text-sm text-gray-500 mt-1">Find your next opportunity from {data?.total ?? "…"} active positions</p>
      </div>

      {/* Search bar */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 flex flex-wrap gap-3 mb-6">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            placeholder="Job title, skills, company..."
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={e => e.key === "Enter" && search(true)}
            className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>
        <div className="relative min-w-[160px]">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            placeholder="Location"
            value={location}
            onChange={e => setLocation(e.target.value)}
            className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>
        <select
          value={jobType}
          onChange={e => setJobType(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none min-w-[130px]"
        >
          {JOB_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
        <button
          onClick={() => search(true)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          Search
        </button>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      ) : data?.items.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <Search className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium">No jobs found</p>
          <p className="text-sm mt-1">Try different keywords or clear filters</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data?.items.map(job => (
              <JobCard key={job.id} job={job} onApply={handleApply} />
            ))}
          </div>

          {/* Pagination */}
          {data && data.pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                className="px-4 py-2 rounded-lg border border-gray-200 text-sm disabled:opacity-40 hover:bg-gray-50"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500">Page {page} of {data.pages}</span>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 rounded-lg border border-gray-200 text-sm disabled:opacity-40 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
