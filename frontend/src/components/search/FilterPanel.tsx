"use client";

import { useState } from "react";
import type {
  EducationTier,
  SearchCandidateRequest,
  SkillFilter,
  SkillMatchMode,
  WorkPreference,
} from "@/types/search";
import {
  EDUCATION_TIER_LABELS,
  WORK_PREFERENCE_LABELS,
} from "@/types/search";

interface Props {
  filters: SearchCandidateRequest;
  onChange: (filters: SearchCandidateRequest) => void;
  onSearch: () => void;
  loading?: boolean;
}

export default function FilterPanel({ filters, onChange, onSearch, loading }: Props) {
  const [expanded, setExpanded] = useState(true);
  const [newSkill, setNewSkill] = useState("");
  const [newSkillYears, setNewSkillYears] = useState("");

  function update(partial: Partial<SearchCandidateRequest>) {
    onChange({ ...filters, ...partial });
  }

  function addSkill() {
    const s = newSkill.trim();
    if (!s) return;
    const sf: SkillFilter = {
      skill: s,
      min_years: newSkillYears ? parseFloat(newSkillYears) : null,
    };
    update({ skills: [...(filters.skills ?? []), sf] });
    setNewSkill("");
    setNewSkillYears("");
  }

  function removeSkill(index: number) {
    const updated = (filters.skills ?? []).filter((_, i) => i !== index);
    update({ skills: updated });
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      addSkill();
    }
  }

  return (
    <aside className="w-72 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <span className="font-semibold text-gray-800 text-sm">Filters</span>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-indigo-600 hover:underline"
        >
          {expanded ? "Collapse" : "Expand"}
        </button>
      </div>

      {expanded && (
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
          {/* Boolean search */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Boolean Search
            </label>
            <input
              type="text"
              placeholder='e.g. "Python AND Django NOT PHP"'
              value={filters.query ?? ""}
              onChange={(e) => update({ query: e.target.value || null })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <p className="text-xs text-gray-400 mt-1">Supports AND, OR, NOT and quoted phrases</p>
          </section>

          {/* Skills */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">Skills</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                placeholder="Skill name"
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <input
                type="number"
                placeholder="Yrs"
                value={newSkillYears}
                onChange={(e) => setNewSkillYears(e.target.value)}
                min={0}
                max={50}
                className="w-16 border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <button
                onClick={addSkill}
                className="px-2 py-1.5 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700"
              >
                +
              </button>
            </div>

            {/* Skill chips */}
            <div className="flex flex-wrap gap-1 mb-2">
              {(filters.skills ?? []).map((sf, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 text-xs px-2 py-1 rounded-full"
                >
                  {sf.skill}
                  {sf.min_years != null && (
                    <span className="text-indigo-400">{sf.min_years}y+</span>
                  )}
                  <button
                    onClick={() => removeSkill(i)}
                    className="text-indigo-400 hover:text-indigo-700 font-bold leading-none"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>

            {(filters.skills ?? []).length > 1 && (
              <div className="flex gap-3">
                {(["AND", "OR"] as SkillMatchMode[]).map((mode) => (
                  <label key={mode} className="flex items-center gap-1 text-xs text-gray-600 cursor-pointer">
                    <input
                      type="radio"
                      name="skill_match"
                      value={mode}
                      checked={(filters.skill_match ?? "AND") === mode}
                      onChange={() => update({ skill_match: mode })}
                      className="accent-indigo-600"
                    />
                    Must have {mode === "AND" ? "ALL" : "ANY"}
                  </label>
                ))}
              </div>
            )}
          </section>

          {/* Experience */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Experience (years)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Min"
                value={filters.experience_min ?? ""}
                onChange={(e) =>
                  update({ experience_min: e.target.value ? parseFloat(e.target.value) : null })
                }
                min={0}
                max={60}
                className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <span className="text-gray-400 text-xs">–</span>
              <input
                type="number"
                placeholder="Max"
                value={filters.experience_max ?? ""}
                onChange={(e) =>
                  update({ experience_max: e.target.value ? parseFloat(e.target.value) : null })
                }
                min={0}
                max={60}
                className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
          </section>

          {/* Location */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">Location</label>
            <input
              type="text"
              placeholder="e.g. Bangalore, Mumbai"
              value={filters.location ?? ""}
              onChange={(e) => update({ location: e.target.value || null })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </section>

          {/* Notice Period */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Notice Period (max days)
            </label>
            <input
              type="number"
              placeholder="e.g. 30"
              value={filters.notice_period_max_days ?? ""}
              onChange={(e) =>
                update({
                  notice_period_max_days: e.target.value ? parseInt(e.target.value) : null,
                })
              }
              min={0}
              max={365}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </section>

          {/* CTC */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Expected CTC (Lakhs INR)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Min"
                value={filters.ctc_min ?? ""}
                onChange={(e) =>
                  update({ ctc_min: e.target.value ? parseInt(e.target.value) : null })
                }
                min={0}
                className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <span className="text-gray-400 text-xs">–</span>
              <input
                type="number"
                placeholder="Max"
                value={filters.ctc_max ?? ""}
                onChange={(e) =>
                  update({ ctc_max: e.target.value ? parseInt(e.target.value) : null })
                }
                min={0}
                className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
          </section>

          {/* Education Tier */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">Education</label>
            <select
              value={filters.education_tier ?? "any"}
              onChange={(e) => update({ education_tier: e.target.value as EducationTier })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              {(Object.keys(EDUCATION_TIER_LABELS) as EducationTier[]).map((key) => (
                <option key={key} value={key}>
                  {EDUCATION_TIER_LABELS[key]}
                </option>
              ))}
            </select>
          </section>

          {/* Work Preference */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Work Preference
            </label>
            <select
              value={filters.work_preference ?? "any"}
              onChange={(e) => update({ work_preference: e.target.value as WorkPreference })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              {(Object.keys(WORK_PREFERENCE_LABELS) as WorkPreference[]).map((key) => (
                <option key={key} value={key}>
                  {WORK_PREFERENCE_LABELS[key]}
                </option>
              ))}
            </select>
          </section>

          {/* Profile Strength */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Min Profile Strength:{" "}
              <span className="text-indigo-600 font-semibold">
                {filters.profile_strength_min ?? 0}%
              </span>
            </label>
            <input
              type="range"
              min={0}
              max={100}
              step={10}
              value={filters.profile_strength_min ?? 0}
              onChange={(e) =>
                update({
                  profile_strength_min: parseInt(e.target.value) || null,
                })
              }
              className="w-full accent-indigo-600"
            />
          </section>

          {/* Last Active */}
          <section>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Last Active (within days)
            </label>
            <select
              value={filters.last_active_days ?? ""}
              onChange={(e) =>
                update({
                  last_active_days: e.target.value ? parseInt(e.target.value) : null,
                })
              }
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              <option value="">Any time</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
              <option value="180">Last 6 months</option>
            </select>
          </section>
        </div>
      )}

      {/* Search button */}
      <div className="px-4 py-3 border-t border-gray-200">
        <button
          onClick={onSearch}
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium text-sm py-2.5 rounded-lg transition-colors"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>
    </aside>
  );
}
