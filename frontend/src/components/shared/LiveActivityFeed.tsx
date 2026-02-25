"use client";

import { useEffect, useRef } from "react";
import type { RealtimeEvent } from "@/hooks/useRealtimeEvents";

// ── Event display config ──────────────────────────────────────────────────────

const EVENT_CONFIG: Record<
  string,
  { icon: string; color: string; label: (p: Record<string, unknown>) => string }
> = {
  new_application: {
    icon: "📋",
    color: "text-green-700 bg-green-50 border-green-200",
    label: (p) => `New application from ${p.candidate_name ?? "a candidate"} for job ${p.job_id?.toString().slice(0, 8)}…`,
  },
  new_candidate_registered: {
    icon: "👤",
    color: "text-blue-700 bg-blue-50 border-blue-200",
    label: (p) => `New candidate registered: ${p.name ?? p.email ?? "someone"}`,
  },
  new_job_posted: {
    icon: "💼",
    color: "text-indigo-700 bg-indigo-50 border-indigo-200",
    label: (p) => `New job posted: ${p.title ?? "Untitled"} ${p.location ? `(${p.location})` : ""}`,
  },
  pipeline_stage_changed: {
    icon: "🔄",
    color: "text-yellow-700 bg-yellow-50 border-yellow-200",
    label: (p) => `Application moved to ${p.new_stage ?? "new stage"}`,
  },
  profile_viewed: {
    icon: "👁",
    color: "text-purple-700 bg-purple-50 border-purple-200",
    label: (p) => `Your profile was viewed${p.viewer_name ? ` by ${p.viewer_name}` : ""}`,
  },
  connected: {
    icon: "🟢",
    color: "text-gray-600 bg-gray-50 border-gray-200",
    label: () => "Real-time connection established",
  },
};

const DEFAULT_CONFIG = {
  icon: "📡",
  color: "text-gray-700 bg-gray-50 border-gray-200",
  label: (p: Record<string, unknown>) =>
    JSON.stringify(p).slice(0, 60) + (JSON.stringify(p).length > 60 ? "…" : ""),
};

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "";
  }
}

// ── Component ─────────────────────────────────────────────────────────────────

interface Props {
  events: RealtimeEvent[];
  maxHeight?: string;
  title?: string;
}

export default function LiveActivityFeed({
  events,
  maxHeight = "320px",
  title = "Live Activity",
}: Props) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to top (newest is first in array)
  useEffect(() => {
    // no-op — newest events are rendered at the top, no scroll needed
  }, [events]);

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-800">{title}</span>
          {events.length > 0 && (
            <span className="text-xs bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full font-medium">
              {events.length}
            </span>
          )}
        </div>
        <span className="text-xs text-gray-400">Live updates</span>
      </div>

      {/* Feed */}
      <div
        className="overflow-y-auto divide-y divide-gray-50"
        style={{ maxHeight }}
      >
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-gray-400">
            <span className="text-2xl mb-2">📡</span>
            <p className="text-sm">Waiting for activity…</p>
          </div>
        ) : (
          events.map((evt, i) => {
            const cfg = EVENT_CONFIG[evt.event_type] ?? DEFAULT_CONFIG;
            return (
              <div
                key={`${evt.timestamp}-${i}`}
                className={`flex items-start gap-3 px-4 py-2.5 ${i === 0 ? "animate-pulse-once" : ""}`}
              >
                <span className="text-lg flex-shrink-0 mt-0.5">{cfg.icon}</span>
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-xs px-2 py-0.5 rounded-md border inline-block font-medium ${cfg.color}`}
                  >
                    {evt.event_type}
                  </p>
                  <p className="text-xs text-gray-700 mt-1 leading-snug">
                    {cfg.label(evt.payload)}
                  </p>
                </div>
                <span className="text-xs text-gray-400 flex-shrink-0 mt-0.5">
                  {formatTime(evt.timestamp)}
                </span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
