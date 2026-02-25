"use client";

import { useEffect, useState } from "react";
import { Zap, RefreshCw } from "lucide-react";
import { aiAPI } from "@/lib/aiAPI";
import type { MatchScore } from "@/types/ai";

const GRADE_COLORS: Record<string, string> = {
  A: "bg-green-100 text-green-800 border-green-300",
  B: "bg-blue-100 text-blue-700 border-blue-300",
  C: "bg-amber-100 text-amber-700 border-amber-300",
  D: "bg-orange-100 text-orange-700 border-orange-300",
  F: "bg-red-100 text-red-700 border-red-300",
};

interface Props {
  applicationId: string;
  compact?: boolean;
}

export default function MatchScoreBadge({ applicationId, compact = false }: Props) {
  const [data, setData] = useState<MatchScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const load = async (refresh = false) => {
    setLoading(true);
    setError(false);
    try {
      const r = await aiAPI.getMatchScore(applicationId, refresh);
      setData(r.data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [applicationId]);

  if (loading) return (
    <span className="inline-flex items-center gap-1 text-xs text-gray-400 animate-pulse">
      <Zap className="w-3 h-3" /> Scoring…
    </span>
  );

  if (error || !data) return (
    <button
      onClick={() => load()}
      className="inline-flex items-center gap-1 text-xs text-indigo-500 hover:text-indigo-700"
    >
      <Zap className="w-3 h-3" /> Score
    </button>
  );

  const gradeClass = GRADE_COLORS[data.grade] || GRADE_COLORS.F;

  if (compact) return (
    <span className={`inline-flex items-center gap-1 text-xs border px-2 py-0.5 rounded-full font-semibold ${gradeClass}`}>
      {data.score}% · {data.grade}
    </span>
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-indigo-500" />
          <span className="text-sm font-semibold text-gray-900">AI Match Score</span>
          {data.cached && <span className="text-xs text-gray-400">(cached)</span>}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-bold border px-2.5 py-1 rounded-full ${gradeClass}`}>
            {data.score}% · Grade {data.grade}
          </span>
          <button
            onClick={() => load(true)}
            className="text-gray-400 hover:text-indigo-500 transition-colors"
            title="Refresh score"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {data.summary && (
        <p className="text-xs text-gray-600 bg-gray-50 rounded-lg p-2">{data.summary}</p>
      )}

      <div className="grid grid-cols-2 gap-3 text-xs">
        {data.matched_skills.length > 0 && (
          <div>
            <p className="text-green-700 font-medium mb-1">Matched Skills</p>
            <div className="flex flex-wrap gap-1">
              {data.matched_skills.map(s => (
                <span key={s} className="bg-green-50 border border-green-200 text-green-700 px-1.5 py-0.5 rounded-full">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
        {data.missing_skills.length > 0 && (
          <div>
            <p className="text-red-600 font-medium mb-1">Missing Skills</p>
            <div className="flex flex-wrap gap-1">
              {data.missing_skills.map(s => (
                <span key={s} className="bg-red-50 border border-red-200 text-red-600 px-1.5 py-0.5 rounded-full">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
