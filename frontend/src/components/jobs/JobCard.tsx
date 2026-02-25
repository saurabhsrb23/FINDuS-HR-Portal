"use client";

import Link from "next/link";

import type { JobListItem, JobType } from "@/types/job";
import {
  JOB_STATUS_COLORS,
  JOB_STATUS_LABELS,
  JOB_TYPE_LABELS,
} from "@/types/job";

interface JobCardProps {
  job: JobListItem;
  onPublish?: (id: string) => void;
  onPause?: (id: string) => void;
  onClone?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function JobCard({
  job,
  onPublish,
  onPause,
  onClone,
  onDelete,
}: JobCardProps) {
  const deadline = job.deadline ? new Date(job.deadline) : null;
  const isOverdue = deadline && deadline < new Date();

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-md transition-shadow flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <Link
            href={`/dashboard/jobs/${job.id}/edit`}
            className="font-semibold text-gray-900 hover:text-indigo-600 line-clamp-1"
          >
            {job.title}
          </Link>
          <p className="text-sm text-gray-500 mt-0.5 line-clamp-1">
            {[job.department, job.location].filter(Boolean).join(" · ")}
          </p>
        </div>
        <span
          className={`flex-shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${JOB_STATUS_COLORS[job.status]}`}
        >
          {JOB_STATUS_LABELS[job.status]}
        </span>
      </div>

      {/* Meta */}
      <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
        <span className="px-2 py-0.5 bg-gray-100 rounded-full">
          {JOB_TYPE_LABELS[job.job_type as JobType]}
        </span>
        {job.skills.slice(0, 3).map((s) => (
          <span
            key={s.id}
            className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full"
          >
            {s.skill_name}
          </span>
        ))}
        {job.skills.length > 3 && (
          <span className="text-gray-400">+{job.skills.length - 3}</span>
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-5 text-sm text-gray-500">
        <span title="Applications">📋 {job.applications_count}</span>
        <span title="Views">👁 {job.views_count}</span>
        {deadline && (
          <span
            className={`text-xs ${isOverdue ? "text-red-500" : "text-gray-400"}`}
            title="Deadline"
          >
            ⏰ {deadline.toLocaleDateString()}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1.5 pt-1 flex-wrap">
        {job.status === "draft" && onPublish && (
          <button
            onClick={() => onPublish(job.id)}
            className="px-2.5 py-1 text-xs bg-green-50 text-green-700 rounded-lg hover:bg-green-100 font-medium"
          >
            Publish
          </button>
        )}
        {job.status === "active" && onPause && (
          <button
            onClick={() => onPause(job.id)}
            className="px-2.5 py-1 text-xs bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 font-medium"
          >
            Pause
          </button>
        )}
        <Link
          href={`/dashboard/jobs/${job.id}/pipeline`}
          className="px-2.5 py-1 text-xs bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 font-medium"
        >
          Pipeline
        </Link>
        <Link
          href={`/dashboard/jobs/${job.id}/questionnaire`}
          className="px-2.5 py-1 text-xs bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 font-medium"
        >
          Questions
        </Link>
        {onClone && (
          <button
            onClick={() => onClone(job.id)}
            className="px-2.5 py-1 text-xs bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 font-medium"
          >
            Clone
          </button>
        )}
        {onDelete && (job.status === "draft" || job.status === "closed") && (
          <button
            onClick={() => onDelete(job.id)}
            className="px-2.5 py-1 text-xs bg-red-50 text-red-600 rounded-lg hover:bg-red-100 font-medium"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
