"use client";

import type { CandidateSearchItem } from "@/types/search";

interface Props {
  candidates: CandidateSearchItem[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onToggleAll: () => void;
}

export default function CandidateTable({
  candidates,
  selectedIds,
  onToggleSelect,
  onToggleAll,
}: Props) {
  const allSelected =
    candidates.length > 0 && candidates.every((c) => selectedIds.has(c.id));

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="w-10 px-3 py-3 text-left">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onToggleAll}
                className="accent-indigo-600 w-4 h-4 cursor-pointer"
                aria-label="Select all"
              />
            </th>
            <th className="px-3 py-3 text-left font-medium text-gray-600">Name</th>
            <th className="px-3 py-3 text-left font-medium text-gray-600">Headline</th>
            <th className="px-3 py-3 text-left font-medium text-gray-600">Location</th>
            <th className="px-3 py-3 text-left font-medium text-gray-600">Exp</th>
            <th className="px-3 py-3 text-left font-medium text-gray-600">Skills</th>
            <th className="px-3 py-3 text-left font-medium text-gray-600">Notice</th>
            <th className="px-3 py-3 text-left font-medium text-gray-600">CTC (L)</th>
            <th className="px-3 py-3 text-left font-medium text-gray-600">Strength</th>
            <th className="px-3 py-3 text-left font-medium text-gray-600">Match</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {candidates.map((c) => (
            <tr
              key={c.id}
              className={`hover:bg-gray-50 transition-colors ${
                selectedIds.has(c.id) ? "bg-indigo-50/40" : ""
              }`}
            >
              <td className="px-3 py-3">
                <input
                  type="checkbox"
                  checked={selectedIds.has(c.id)}
                  onChange={() => onToggleSelect(c.id)}
                  className="accent-indigo-600 w-4 h-4 cursor-pointer"
                  aria-label={`Select ${c.full_name}`}
                />
              </td>
              <td className="px-3 py-3 font-medium text-gray-900 whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 flex-shrink-0 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-xs font-bold">
                    {c.full_name?.charAt(0).toUpperCase() ?? "?"}
                  </div>
                  <span className="truncate max-w-[120px]">{c.full_name ?? "—"}</span>
                </div>
              </td>
              <td className="px-3 py-3 text-gray-600 max-w-[180px]">
                <span className="truncate block">{c.headline ?? "—"}</span>
              </td>
              <td className="px-3 py-3 text-gray-600 whitespace-nowrap">
                {c.location ?? "—"}
              </td>
              <td className="px-3 py-3 text-gray-700 whitespace-nowrap">
                {c.years_of_experience != null ? `${c.years_of_experience}y` : "—"}
              </td>
              <td className="px-3 py-3">
                <div className="flex flex-wrap gap-1 max-w-[200px]">
                  {c.skills.slice(0, 3).map((s) => (
                    <span
                      key={s.skill_name}
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        s.matched
                          ? "bg-indigo-100 text-indigo-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {s.skill_name}
                    </span>
                  ))}
                  {c.skills.length > 3 && (
                    <span className="text-xs text-gray-400">+{c.skills.length - 3}</span>
                  )}
                </div>
              </td>
              <td className="px-3 py-3 text-gray-600 whitespace-nowrap">
                {c.notice_period_days != null ? `${c.notice_period_days}d` : "—"}
              </td>
              <td className="px-3 py-3 text-gray-600 whitespace-nowrap">
                {c.desired_salary_min != null || c.desired_salary_max != null ? (
                  <span>
                    {c.desired_salary_min != null
                      ? `${(c.desired_salary_min / 100000).toFixed(0)}`
                      : ""}
                    {c.desired_salary_min != null && c.desired_salary_max != null && "–"}
                    {c.desired_salary_max != null
                      ? `${(c.desired_salary_max / 100000).toFixed(0)}`
                      : ""}
                  </span>
                ) : (
                  "—"
                )}
              </td>
              <td className="px-3 py-3">
                <div className="flex items-center gap-1.5">
                  <div className="w-16 bg-gray-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${
                        c.profile_strength >= 80
                          ? "bg-green-500"
                          : c.profile_strength >= 50
                          ? "bg-yellow-500"
                          : "bg-red-400"
                      }`}
                      style={{ width: `${c.profile_strength}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500">{c.profile_strength}%</span>
                </div>
              </td>
              <td className="px-3 py-3">
                {c.match_score != null ? (
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      c.match_score >= 75
                        ? "bg-green-100 text-green-700"
                        : c.match_score >= 50
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {c.match_score}%
                  </span>
                ) : (
                  <span className="text-gray-400 text-xs">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {candidates.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🔍</p>
          <p className="font-medium">No candidates found</p>
          <p className="text-sm mt-1">Try adjusting your filters</p>
        </div>
      )}
    </div>
  );
}
