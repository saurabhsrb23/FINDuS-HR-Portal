"use client";

import { useState } from "react";
import { X, Users, Trophy, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { aiAPI } from "@/lib/aiAPI";
import type { CandidateComparison } from "@/types/ai";

interface Props {
  applicationIds: string[];
  candidateNames: string[];
  onClose: () => void;
}

export default function ComparisonModal({ applicationIds, candidateNames, onClose }: Props) {
  const [data, setData] = useState<CandidateComparison | null>(null);
  const [loading, setLoading] = useState(false);

  const compare = async () => {
    if (applicationIds.length < 2) {
      toast.error("Select at least 2 candidates to compare");
      return;
    }
    setLoading(true);
    try {
      const r = await aiAPI.compareCandidates(applicationIds);
      setData(r.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "AI comparison failed");
    } finally {
      setLoading(false);
    }
  };

  useState(() => { compare(); });

  const scoreColor = (s: number) =>
    s >= 80 ? "text-green-600" : s >= 60 ? "text-amber-600" : "text-red-600";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-gray-900">AI Candidate Comparison</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-3" />
              <p className="text-sm">AI is comparing candidates…</p>
            </div>
          ) : data ? (
            <div className="space-y-6">
              {/* Comparison table */}
              <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${data.candidates.length}, 1fr)` }}>
                {data.candidates.map((c, i) => (
                  <div key={i} className="bg-gray-50 rounded-xl p-4 space-y-3">
                    <div>
                      <p className="font-semibold text-gray-900 text-sm truncate">{c.name || candidateNames[i] || `Candidate ${i + 1}`}</p>
                      <p className={`text-2xl font-bold mt-1 ${scoreColor(c.score)}`}>{c.score}%</p>
                    </div>

                    {c.top_skills?.length > 0 && (
                      <div>
                        <p className="text-xs text-gray-500 font-medium mb-1">Top Skills</p>
                        <div className="flex flex-wrap gap-1">
                          {c.top_skills.slice(0, 4).map(s => (
                            <span key={s} className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 px-1.5 py-0.5 rounded-full">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {c.pros?.length > 0 && (
                      <div>
                        <p className="text-xs text-green-700 font-medium mb-1">Pros</p>
                        <ul className="space-y-0.5">
                          {c.pros.map((p, j) => (
                            <li key={j} className="text-xs text-gray-600">✓ {p}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {c.cons?.length > 0 && (
                      <div>
                        <p className="text-xs text-red-600 font-medium mb-1">Cons</p>
                        <ul className="space-y-0.5">
                          {c.cons.map((p, j) => (
                            <li key={j} className="text-xs text-gray-600">✗ {p}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* AI recommendation */}
              {data.recommendation && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Trophy className="w-4 h-4 text-indigo-600" />
                    <p className="text-sm font-semibold text-indigo-800">AI Recommendation</p>
                  </div>
                  <p className="text-sm text-gray-700">{data.recommendation}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-10 text-gray-400">
              <button onClick={compare} className="bg-indigo-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-indigo-700">
                Run Comparison
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
