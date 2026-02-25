"use client";

import type { CandidateSearchItem } from "@/types/search";

interface Props {
  candidate: CandidateSearchItem;
  selected: boolean;
  onToggleSelect: (id: string) => void;
}

function ProfileStrengthBar({ value }: { value: number }) {
  const color =
    value >= 80
      ? "bg-green-500"
      : value >= 50
      ? "bg-yellow-500"
      : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-gray-500">{value}%</span>
    </div>
  );
}

export default function CandidateCard({ candidate, selected, onToggleSelect }: Props) {
  const c = candidate;

  return (
    <div
      className={`bg-white border rounded-xl p-4 flex gap-3 hover:shadow-md transition-shadow ${
        selected ? "border-indigo-400 bg-indigo-50/30" : "border-gray-200"
      }`}
    >
      {/* Checkbox */}
      <div className="pt-0.5">
        <input
          type="checkbox"
          checked={selected}
          onChange={() => onToggleSelect(c.id)}
          className="w-4 h-4 accent-indigo-600 cursor-pointer"
          aria-label={`Select ${c.full_name}`}
        />
      </div>

      {/* Avatar */}
      <div className="w-10 h-10 flex-shrink-0 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-base">
        {c.full_name?.charAt(0).toUpperCase() ?? "?"}
      </div>

      {/* Main info */}
      <div className="flex-1 min-w-0">
        {/* Name + match score */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-gray-900 text-sm truncate">
            {c.full_name ?? "Unknown"}
          </h3>
          {c.match_score != null && (
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0 ${
                c.match_score >= 75
                  ? "bg-green-100 text-green-700"
                  : c.match_score >= 50
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              {c.match_score}% match
            </span>
          )}
        </div>

        {/* Headline */}
        {c.headline && (
          <p className="text-xs text-gray-600 mt-0.5 truncate">{c.headline}</p>
        )}

        {/* Location + experience */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-xs text-gray-500">
          {c.location && <span>📍 {c.location}</span>}
          {c.years_of_experience != null && (
            <span>💼 {c.years_of_experience}y exp</span>
          )}
          {c.notice_period_days != null && (
            <span>⏱ {c.notice_period_days}d notice</span>
          )}
          {c.open_to_remote && (
            <span className="text-green-600">🌐 Remote OK</span>
          )}
        </div>

        {/* Skills */}
        {c.skills.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {c.skills.slice(0, 6).map((s) => (
              <span
                key={s.skill_name}
                className={`text-xs px-2 py-0.5 rounded-full ${
                  s.matched
                    ? "bg-indigo-100 text-indigo-700 font-medium"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {s.skill_name}
              </span>
            ))}
            {c.skills.length > 6 && (
              <span className="text-xs text-gray-400 px-1 py-0.5">
                +{c.skills.length - 6} more
              </span>
            )}
          </div>
        )}

        {/* Education */}
        {c.education_summary && (
          <p className="text-xs text-gray-500 mt-1.5">🎓 {c.education_summary}</p>
        )}

        {/* CTC */}
        {(c.desired_salary_min != null || c.desired_salary_max != null) && (
          <p className="text-xs text-gray-500 mt-1">
            💰{" "}
            {c.desired_salary_min != null
              ? `₹${(c.desired_salary_min / 100000).toFixed(1)}L`
              : ""}
            {c.desired_salary_min != null && c.desired_salary_max != null && " – "}
            {c.desired_salary_max != null
              ? `₹${(c.desired_salary_max / 100000).toFixed(1)}L`
              : ""}
          </p>
        )}

        {/* AI snippet */}
        {c.ai_summary_snippet && (
          <p className="text-xs text-indigo-600 mt-1.5 italic line-clamp-2">
            ✨ {c.ai_summary_snippet}
          </p>
        )}

        {/* Profile strength */}
        <div className="mt-2">
          <ProfileStrengthBar value={c.profile_strength} />
        </div>
      </div>
    </div>
  );
}
