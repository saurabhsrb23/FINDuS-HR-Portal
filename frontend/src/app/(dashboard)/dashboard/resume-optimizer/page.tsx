"use client";

import { useState, useEffect } from "react";
import { Sparkles, Loader2, RefreshCw, Target, Zap, Shield, CheckCircle, AlertCircle } from "lucide-react";
import { aiAPI } from "@/lib/aiAPI";
import type { ResumeOptimizer } from "@/types/ai";

export default function ResumeOptimizerPage() {
  const [data, setData] = useState<ResumeOptimizer | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (force = false) => {
    if (force) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const r = await aiAPI.optimizeResume(force);
      setData(r.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(msg || "Failed to analyze resume. Please complete your profile first.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const scoreColor = (s: number) =>
    s >= 80 ? "#22c55e" : s >= 60 ? "#f59e0b" : "#ef4444";

  const scoreLabel = (s: number) =>
    s >= 80 ? "Excellent" : s >= 60 ? "Good" : "Needs work";

  function ScoreRing({
    score,
    label,
    icon: Icon,
  }: {
    score: number;
    label: string;
    icon: React.ElementType;
  }) {
    const r = 26;
    const circ = 2 * Math.PI * r;
    const offset = circ - (score / 100) * circ;
    const color = scoreColor(score);

    return (
      <div className="flex flex-col items-center gap-2">
        <div className="relative w-16 h-16">
          <svg width="64" height="64" className="-rotate-90">
            <circle cx="32" cy="32" r={r} stroke="#e5e7eb" strokeWidth="5" fill="none" />
            <circle
              cx="32" cy="32" r={r}
              stroke={color} strokeWidth="5" fill="none"
              strokeDasharray={circ}
              strokeDashoffset={offset}
              strokeLinecap="round"
              style={{ transition: "stroke-dashoffset 0.6s ease" }}
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-gray-800">
            {score}
          </span>
        </div>
        <div className="text-center">
          <Icon className="w-3.5 h-3.5 mx-auto mb-0.5" style={{ color }} />
          <p className="text-xs text-gray-600 font-medium">{label}</p>
          <p className="text-xs" style={{ color }}>{scoreLabel(score)}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-64 text-gray-400">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm">AI is analyzing your resume…</p>
        <p className="text-xs mt-1 text-gray-300">This may take a few seconds</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-2xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-red-700 text-sm font-medium mb-1">Analysis failed</p>
          <p className="text-red-500 text-xs mb-4">{error}</p>
          <button
            onClick={() => load()}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-8 max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-600" />
            Resume Optimizer
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            AI-powered analysis to help you land more interviews
            {data.cached && (
              <span className="ml-2 text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">
                cached
              </span>
            )}
          </p>
        </div>
        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-800 border border-indigo-200 rounded-lg px-3 py-2 hover:bg-indigo-50 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
          {refreshing ? "Analyzing…" : "Refresh"}
        </button>
      </div>

      {/* Score cards */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-6 text-center">Score Breakdown</h2>
        <div className="flex justify-around">
          <ScoreRing score={data.overall_score} label="Overall" icon={Target} />
          <ScoreRing score={data.ats_score} label="ATS Friendly" icon={Shield} />
          <ScoreRing score={data.impact_score} label="Impact" icon={Zap} />
        </div>
      </div>

      {/* Strong / Weak sections */}
      <div className="grid sm:grid-cols-2 gap-4">
        {data.strong_sections?.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-green-800 mb-3 flex items-center gap-1">
              <CheckCircle className="w-4 h-4" />
              Strong Sections
            </h2>
            <ul className="space-y-1">
              {data.strong_sections.map((s, i) => (
                <li key={i} className="text-sm text-green-700">✓ {s}</li>
              ))}
            </ul>
          </div>
        )}

        {data.weak_sections?.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-red-700 mb-3 flex items-center gap-1">
              <AlertCircle className="w-4 h-4" />
              Needs Improvement
            </h2>
            <ul className="space-y-1">
              {data.weak_sections.map((s, i) => (
                <li key={i} className="text-sm text-red-600">✗ {s}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Tips */}
      {data.tips?.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">
            Improvement Tips
          </h2>
          <ul className="space-y-2">
            {data.tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-gray-700">
                <span className="mt-0.5 bg-indigo-100 text-indigo-700 rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {i + 1}
                </span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
