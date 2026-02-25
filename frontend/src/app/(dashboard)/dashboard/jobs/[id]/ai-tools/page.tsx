"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import {
  Brain,
  Trophy,
  FileText,
  Mail,
  Loader2,
  RefreshCw,
  Copy,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { aiAPI } from "@/lib/aiAPI";
import type { GenerateJDRequest, GeneratedJD, RankingResult } from "@/types/ai";

type Tab = "ranking" | "jd" | "rejection";

export default function AIToolsPage() {
  const params = useParams();
  const jobId = params.id as string;
  const [tab, setTab] = useState<Tab>("ranking");

  // ── Ranking ──────────────────────────────────────────────────────────────
  const [ranking, setRanking] = useState<RankingResult | null>(null);
  const [rankLoading, setRankLoading] = useState(false);

  const loadRanking = useCallback(
    async (enqueue = false) => {
      setRankLoading(true);
      try {
        if (enqueue) {
          await aiAPI.queueRanking(jobId);
          toast.success("Ranking queued — fetching in 4 s…");
          await new Promise((r) => setTimeout(r, 4000));
        }
        const r = await aiAPI.getRanking(jobId);
        setRanking(r.data);
      } catch {
        if (!enqueue) {
          // No cached ranking yet — that's fine
          setRanking(null);
        } else {
          toast.error("Ranking not ready yet, try again in a moment.");
        }
      } finally {
        setRankLoading(false);
      }
    },
    [jobId]
  );

  useEffect(() => {
    if (tab === "ranking") loadRanking();
  }, [tab, loadRanking]);

  // ── JD Generator ─────────────────────────────────────────────────────────
  const [jdForm, setJdForm] = useState<GenerateJDRequest>({
    role: "",
    department: "",
    keywords: [],
    experience_years: 3,
    location: "",
    job_type: "full_time",
  });
  const [jdResult, setJdResult] = useState<GeneratedJD | null>(null);
  const [jdLoading, setJdLoading] = useState(false);

  const generateJD = async () => {
    setJdLoading(true);
    setJdResult(null);
    try {
      const r = await aiAPI.generateJD(jdForm);
      setJdResult(r.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(msg || "JD generation failed");
    } finally {
      setJdLoading(false);
    }
  };

  // ── Rejection Email ───────────────────────────────────────────────────────
  const [rejAppId, setRejAppId] = useState("");
  const [rejReason, setRejReason] = useState("");
  const [rejResult, setRejResult] = useState<{ subject: string; body: string } | null>(null);
  const [rejLoading, setRejLoading] = useState(false);

  const draftRejection = async () => {
    setRejLoading(true);
    setRejResult(null);
    try {
      const r = await aiAPI.draftRejectionEmail(rejAppId, rejReason || undefined);
      setRejResult(r.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(msg || "Email drafting failed");
    } finally {
      setRejLoading(false);
    }
  };

  // ── Copy helper ───────────────────────────────────────────────────────────
  const [copied, setCopied] = useState(false);
  const copyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: "ranking", label: "Rank Applicants", icon: Trophy },
    { id: "jd", label: "Generate JD", icon: FileText },
    { id: "rejection", label: "Rejection Email", icon: Mail },
  ];

  const scoreColor = (s: number) =>
    s >= 80 ? "text-green-600" : s >= 60 ? "text-amber-600" : "text-red-600";

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-6">
        <Brain className="w-6 h-6 text-indigo-600" />
        AI Tools
      </h1>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-6">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.id
                ? "bg-white text-indigo-700 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Ranking tab ─────────────────────────────────────────────────────── */}
      {tab === "ranking" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              AI-ranked list of all applicants for this job
            </p>
            <button
              onClick={() => loadRanking(true)}
              disabled={rankLoading}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {rankLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Rank Now
            </button>
          </div>

          {rankLoading ? (
            <div className="flex flex-col items-center py-12 text-gray-400">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-2" />
              <p className="text-sm">AI is ranking candidates…</p>
            </div>
          ) : ranking && ranking.ranked.length > 0 ? (
            <div className="space-y-3">
              <p className="text-xs text-gray-500">
                {ranking.total} applicant{ranking.total !== 1 ? "s" : ""} ranked
              </p>
              {ranking.ranked.map((r) => (
                <div
                  key={r.application_id}
                  className="bg-white rounded-xl border border-gray-200 p-4 flex items-start gap-4"
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                      r.rank === 1
                        ? "bg-yellow-100 text-yellow-700"
                        : r.rank === 2
                        ? "bg-gray-100 text-gray-600"
                        : r.rank === 3
                        ? "bg-amber-50 text-amber-700"
                        : "bg-indigo-50 text-indigo-600"
                    }`}
                  >
                    #{r.rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center">
                      <p className="text-xs text-gray-400 truncate font-mono">
                        {r.application_id}
                      </p>
                      <span className={`text-sm font-bold ${scoreColor(r.score)}`}>
                        {r.score}%
                      </span>
                    </div>
                    {r.reason && (
                      <p className="text-xs text-gray-500 mt-0.5">{r.reason}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400 text-sm">
              No ranking yet. Click &ldquo;Rank Now&rdquo; to generate AI rankings.
            </div>
          )}
        </div>
      )}

      {/* ── JD Generator tab ─────────────────────────────────────────────────── */}
      {tab === "jd" && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-600 font-medium mb-1 block">
                Job Role *
              </label>
              <input
                value={jdForm.role}
                onChange={(e) =>
                  setJdForm((f) => ({ ...f, role: e.target.value }))
                }
                placeholder="e.g. Senior React Developer"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium mb-1 block">
                Department
              </label>
              <input
                value={jdForm.department ?? ""}
                onChange={(e) =>
                  setJdForm((f) => ({ ...f, department: e.target.value }))
                }
                placeholder="e.g. Engineering"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-600 font-medium mb-1 block">
                Location
              </label>
              <input
                value={jdForm.location ?? ""}
                onChange={(e) =>
                  setJdForm((f) => ({ ...f, location: e.target.value }))
                }
                placeholder="e.g. Bangalore / Remote"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium mb-1 block">
                Experience (years)
              </label>
              <input
                type="number"
                min={0}
                max={30}
                value={jdForm.experience_years ?? ""}
                onChange={(e) =>
                  setJdForm((f) => ({
                    ...f,
                    experience_years: Number(e.target.value),
                  }))
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-600 font-medium mb-1 block">
              Keywords (comma-separated)
            </label>
            <input
              value={jdForm.keywords.join(", ")}
              onChange={(e) =>
                setJdForm((f) => ({
                  ...f,
                  keywords: e.target.value
                    .split(",")
                    .map((k) => k.trim())
                    .filter(Boolean),
                }))
              }
              placeholder="React, TypeScript, Node.js, PostgreSQL"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs text-gray-600 font-medium mb-1 block">
              Job Type
            </label>
            <select
              value={jdForm.job_type ?? "full_time"}
              onChange={(e) =>
                setJdForm((f) => ({ ...f, job_type: e.target.value }))
              }
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
            </select>
          </div>

          <button
            onClick={generateJD}
            disabled={jdLoading || !jdForm.role}
            className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            {jdLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Brain className="w-4 h-4" />
            )}
            Generate Job Description
          </button>

          {jdResult && (
            <div className="space-y-4">
              {(
                [
                  { key: "title", label: "Title" },
                  { key: "description", label: "Overview" },
                  { key: "responsibilities", label: "Responsibilities" },
                  { key: "requirements", label: "Requirements" },
                  { key: "benefits", label: "Benefits" },
                ] as { key: keyof GeneratedJD; label: string }[]
              ).map(({ key, label }) =>
                jdResult[key] ? (
                  <div key={key} className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                    <div className="flex justify-between items-center mb-2">
                      <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                        {label}
                      </p>
                      <button
                        onClick={() => copyText(String(jdResult[key]))}
                        className="text-gray-400 hover:text-gray-700"
                      >
                        {copied ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                      {String(jdResult[key])}
                    </pre>
                  </div>
                ) : null
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Rejection Email tab ───────────────────────────────────────────────── */}
      {tab === "rejection" && (
        <div className="space-y-5">
          <p className="text-sm text-gray-600">
            Provide the application ID to draft a professional, empathetic
            rejection email.
          </p>

          <div>
            <label className="text-xs text-gray-600 font-medium mb-1 block">
              Application ID *
            </label>
            <input
              value={rejAppId}
              onChange={(e) => setRejAppId(e.target.value)}
              placeholder="UUID from the applications list"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
            />
          </div>

          <div>
            <label className="text-xs text-gray-600 font-medium mb-1 block">
              Rejection Reason (optional)
            </label>
            <textarea
              rows={3}
              value={rejReason}
              onChange={(e) => setRejReason(e.target.value)}
              placeholder="e.g. overqualified, moved forward with another candidate, budget freeze…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
          </div>

          <button
            onClick={draftRejection}
            disabled={rejLoading || !rejAppId.trim()}
            className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            {rejLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Mail className="w-4 h-4" />
            )}
            Draft Rejection Email
          </button>

          {rejResult && (
            <div className="space-y-3">
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                <div className="flex justify-between items-center mb-1">
                  <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    Subject
                  </p>
                  <button
                    onClick={() => copyText(rejResult.subject)}
                    className="text-gray-400 hover:text-gray-700"
                  >
                    {copied ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                </div>
                <p className="text-sm text-gray-700 font-medium">{rejResult.subject}</p>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 relative">
                <div className="flex justify-between items-center mb-2">
                  <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    Email Body
                  </p>
                  <button
                    onClick={() => copyText(rejResult.body)}
                    className="text-gray-400 hover:text-gray-700"
                  >
                    {copied ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                </div>
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {rejResult.body}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
