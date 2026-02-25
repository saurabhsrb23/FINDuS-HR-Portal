"use client";

import { useState, useEffect, useRef } from "react";
import {
  Sparkles, Loader2, RefreshCw, Target, Zap, Shield,
  CheckCircle, AlertCircle, Upload, FileText, Star, BookOpen,
} from "lucide-react";
import { aiAPI } from "@/lib/aiAPI";
import { candidateAPI } from "@/lib/candidateAPI";
import type { ResumeOptimizer, ResumeSummary } from "@/types/ai";

type Tab = "score" | "summary";

// ── Score ring SVG ────────────────────────────────────────────────────────────
function ScoreRing({ score, label, icon: Icon }: {
  score: number; label: string; icon: React.ElementType;
}) {
  const r = 26;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#22c55e" : score >= 60 ? "#f59e0b" : "#ef4444";
  const lbl = score >= 80 ? "Excellent" : score >= 60 ? "Good" : "Needs work";
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-16 h-16">
        <svg width="64" height="64" className="-rotate-90">
          <circle cx="32" cy="32" r={r} stroke="#e5e7eb" strokeWidth="5" fill="none" />
          <circle cx="32" cy="32" r={r} stroke={color} strokeWidth="5" fill="none"
            strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.6s ease" }} />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-gray-800">
          {score}
        </span>
      </div>
      <div className="text-center">
        <Icon className="w-3.5 h-3.5 mx-auto mb-0.5" style={{ color }} />
        <p className="text-xs text-gray-600 font-medium">{label}</p>
        <p className="text-xs" style={{ color }}>{lbl}</p>
      </div>
    </div>
  );
}

export default function ResumeOptimizerPage() {
  const [tab, setTab] = useState<Tab>("score");

  // Score analysis state
  const [scoreData, setScoreData] = useState<ResumeOptimizer | null>(null);
  const [scoreLoading, setScoreLoading] = useState(true);
  const [scoreError, setScoreError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // AI summary state
  const [summaryData, setSummaryData] = useState<ResumeSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // ── Loaders ────────────────────────────────────────────────────────────────

  const loadScore = async (force = false) => {
    if (force) setRefreshing(true);
    else setScoreLoading(true);
    setScoreError(null);
    try {
      const r = await aiAPI.optimizeResume(force);
      setScoreData(r.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setScoreError(msg || "Failed to analyze. Please complete your profile first.");
    } finally {
      setScoreLoading(false);
      setRefreshing(false);
    }
  };

  const loadSummary = async (force = false) => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const r = await aiAPI.getMyResumeSummary(force);
      setSummaryData(r.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setSummaryError(msg || "Failed to generate summary. Upload a resume first.");
    } finally {
      setSummaryLoading(false);
    }
  };

  useEffect(() => { loadScore(); }, []);

  // Load summary when user switches to that tab (lazy load)
  const handleTabSwitch = (t: Tab) => {
    setTab(t);
    if (t === "summary" && !summaryData && !summaryLoading) {
      loadSummary();
    }
  };

  // ── Upload resume then re-analyze ─────────────────────────────────────────

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg(null);
    try {
      await candidateAPI.uploadResume(file);
      setUploadMsg("Resume uploaded! Re-analyzing…");
      // Refresh both analyses after upload
      await loadScore(true);
      if (tab === "summary" || summaryData) await loadSummary(true);
      setUploadMsg("Analysis updated with your new resume.");
      setTimeout(() => setUploadMsg(null), 4000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setUploadMsg(msg || "Upload failed. PDF only, max 5 MB.");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="p-6 max-w-3xl space-y-5">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-600" />
            Resume Optimizer
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            AI-powered analysis to help you land more interviews
          </p>
        </div>

        {/* Upload + Refresh */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {uploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            {uploading ? "Uploading…" : "Upload Resume & Analyze"}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleUpload}
          />

          <button
            onClick={() => tab === "score" ? loadScore(true) : loadSummary(true)}
            disabled={refreshing || scoreLoading || summaryLoading || uploading}
            className="flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-800 border border-indigo-200 rounded-lg px-3 py-2 hover:bg-indigo-50 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${(refreshing || scoreLoading || summaryLoading) ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Upload status */}
      {uploadMsg && (
        <div className={`text-sm px-4 py-2.5 rounded-lg border ${
          uploadMsg.includes("failed") || uploadMsg.includes("Failed")
            ? "bg-red-50 text-red-700 border-red-200"
            : "bg-green-50 text-green-700 border-green-200"
        }`}>
          {uploadMsg}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 gap-1">
        {([ ["score", FileText, "Score Analysis"], ["summary", BookOpen, "AI Summary"] ] as const).map(
          ([key, Icon, label]) => (
            <button
              key={key}
              onClick={() => handleTabSwitch(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === key
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          )
        )}
      </div>

      {/* ── Tab: Score Analysis ────────────────────────────────────────────── */}
      {tab === "score" && (
        <>
          {scoreLoading ? (
            <div className="flex flex-col items-center justify-center min-h-48 text-gray-400">
              <Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-3" />
              <p className="text-sm">AI is analyzing your resume…</p>
            </div>
          ) : scoreError ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <p className="text-red-700 text-sm font-medium mb-1">Analysis failed</p>
              <p className="text-red-500 text-xs mb-4">{scoreError}</p>
              <button onClick={() => loadScore()} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700">
                Try Again
              </button>
            </div>
          ) : scoreData ? (
            <div className="space-y-4">
              {/* Score rings */}
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="text-sm font-semibold text-gray-700">Score Breakdown</h2>
                  {scoreData.cached && (
                    <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">cached</span>
                  )}
                </div>
                <div className="flex justify-around">
                  <ScoreRing score={scoreData.overall_score} label="Overall" icon={Target} />
                  <ScoreRing score={scoreData.ats_score} label="ATS Friendly" icon={Shield} />
                  <ScoreRing score={scoreData.impact_score} label="Impact" icon={Zap} />
                </div>
              </div>

              {/* Strong / Weak */}
              <div className="grid sm:grid-cols-2 gap-4">
                {scoreData.strong_sections?.length > 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-xl p-5">
                    <h2 className="text-sm font-semibold text-green-800 mb-3 flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" /> Strong Sections
                    </h2>
                    <ul className="space-y-1">
                      {scoreData.strong_sections.map((s, i) => (
                        <li key={i} className="text-sm text-green-700">✓ {s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {scoreData.weak_sections?.length > 0 && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-5">
                    <h2 className="text-sm font-semibold text-red-700 mb-3 flex items-center gap-1">
                      <AlertCircle className="w-4 h-4" /> Needs Improvement
                    </h2>
                    <ul className="space-y-1">
                      {scoreData.weak_sections.map((s, i) => (
                        <li key={i} className="text-sm text-red-600">✗ {s}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Tips */}
              {scoreData.tips?.length > 0 && (
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
                  <h2 className="text-sm font-semibold text-gray-700 mb-3">Improvement Tips</h2>
                  <ul className="space-y-2">
                    {scoreData.tips.map((tip, i) => (
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
          ) : null}
        </>
      )}

      {/* ── Tab: AI Summary ───────────────────────────────────────────────── */}
      {tab === "summary" && (
        <>
          {summaryLoading ? (
            <div className="flex flex-col items-center justify-center min-h-48 text-gray-400">
              <Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-3" />
              <p className="text-sm">Generating your AI resume summary…</p>
              <p className="text-xs mt-1 text-gray-300">This may take a few seconds</p>
            </div>
          ) : summaryError ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <p className="text-red-700 text-sm font-medium mb-1">Summary unavailable</p>
              <p className="text-red-500 text-xs mb-4">{summaryError}</p>
              <button onClick={() => loadSummary(true)} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700">
                Try Again
              </button>
            </div>
          ) : summaryData ? (
            <div className="space-y-4">
              {/* Professional Summary */}
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-500" />
                    AI-Generated Professional Summary
                  </h2>
                  {summaryData.cached && (
                    <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">cached</span>
                  )}
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{summaryData.summary}</p>
              </div>

              {/* Experience + Top Skills */}
              <div className="grid sm:grid-cols-2 gap-4">
                {summaryData.experience_years != null && (
                  <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-5">
                    <h3 className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-2">
                      Total Experience
                    </h3>
                    <p className="text-3xl font-bold text-indigo-600">
                      {summaryData.experience_years}
                      <span className="text-base font-normal text-indigo-500 ml-1">years</span>
                    </p>
                  </div>
                )}

                {summaryData.top_skills?.length > 0 && (
                  <div className="bg-white border border-gray-200 rounded-xl p-5">
                    <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1">
                      <Star className="w-3.5 h-3.5 text-amber-500" /> Top Skills
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {summaryData.top_skills.map((s, i) => (
                        <span key={i} className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-1 rounded-full font-medium">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Strengths */}
              {summaryData.strengths?.length > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-green-800 mb-3 flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" /> Key Strengths
                  </h3>
                  <ul className="space-y-1.5">
                    {summaryData.strengths.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-green-700">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5 flex-shrink-0" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
