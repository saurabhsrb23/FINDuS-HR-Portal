"use client";

import { useEffect, useState } from "react";
import { Brain, RefreshCw, Star } from "lucide-react";
import { aiAPI } from "@/lib/aiAPI";
import type { ResumeSummary } from "@/types/ai";

interface Props {
  candidateId: string;
}

export default function AISummaryPanel({ candidateId }: Props) {
  const [data, setData] = useState<ResumeSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const r = await aiAPI.getResumeSummary(candidateId, refresh);
      setData(r.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to generate AI summary");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [candidateId]);

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-indigo-600" />
          <span className="font-semibold text-indigo-900">AI Candidate Summary</span>
          {data?.cached && <span className="text-xs text-indigo-400">(cached)</span>}
        </div>
        {!loading && (
          <button
            onClick={() => load(true)}
            className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800"
          >
            <RefreshCw className="w-3 h-3" /> Regenerate
          </button>
        )}
      </div>

      {loading ? (
        <div className="space-y-2 animate-pulse">
          <div className="h-3 bg-indigo-200 rounded w-full" />
          <div className="h-3 bg-indigo-200 rounded w-5/6" />
          <div className="h-3 bg-indigo-200 rounded w-4/6" />
          <p className="text-xs text-indigo-400 text-center pt-1">Generating AI summary…</p>
        </div>
      ) : error ? (
        <div className="text-sm text-red-600 bg-red-50 rounded-lg p-3">
          {error}
          <button onClick={() => load()} className="ml-2 underline text-xs">Retry</button>
        </div>
      ) : data ? (
        <>
          <p className="text-sm text-gray-700 leading-relaxed">{data.summary}</p>

          {data.strengths.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-2">
                Key Strengths
              </p>
              <div className="space-y-1">
                {data.strengths.map((s, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <Star className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" />
                    {s}
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.top_skills.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-2">
                Top Skills
              </p>
              <div className="flex flex-wrap gap-1.5">
                {data.top_skills.map(s => (
                  <span
                    key={s}
                    className="text-xs bg-white border border-indigo-200 text-indigo-700 px-2 py-0.5 rounded-full"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {data.experience_years != null && (
            <p className="text-xs text-gray-500">
              Experience: <span className="font-medium text-gray-700">{data.experience_years} years</span>
            </p>
          )}
        </>
      ) : null}
    </div>
  );
}
