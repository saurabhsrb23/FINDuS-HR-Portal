"use client";

import { useEffect, useRef, useState } from "react";
import { adminAPI } from "@/lib/adminAPI";
import type { PlatformEventItem } from "@/types/admin";

const EVENT_COLOR: Record<string, string> = {
  admin_login: "border-l-emerald-500",
  admin_account_locked: "border-l-red-500",
  admin_created: "border-l-indigo-500",
  admin_deleted: "border-l-rose-500",
  user_deactivated: "border-l-amber-500",
  company_status_updated: "border-l-purple-500",
  announcement_sent: "border-l-teal-500",
  error: "border-l-red-400",
};

export function RealTimeEventFeed() {
  const [events, setEvents] = useState<PlatformEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const seenIdsRef = useRef<Set<string>>(new Set());

  async function poll() {
    try {
      const res = await adminAPI.listEvents({ page: 1, page_size: 20 });
      const newItems = res.items.filter((e) => !seenIdsRef.current.has(e.id));
      if (newItems.length > 0) {
        newItems.forEach((e) => seenIdsRef.current.add(e.id));
        setEvents((prev) => [...newItems, ...prev].slice(0, 50));
      }
    } catch {
      // silently ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    poll();
    intervalRef.current = setInterval(poll, 10000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-gray-300 font-medium text-sm uppercase tracking-wide">
          Real-Time Event Feed
        </h2>
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse inline-block" />
          Live (10s poll)
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden max-h-72 overflow-y-auto">
        {loading ? (
          <div className="p-6 text-center text-gray-500 text-sm">Loading events…</div>
        ) : events.length === 0 ? (
          <div className="p-6 text-center text-gray-500 text-sm">No events recorded yet</div>
        ) : (
          <div className="divide-y divide-gray-800/50">
            {events.map((e) => (
              <div
                key={e.id}
                className={`flex items-start gap-3 px-4 py-3 border-l-2 ${
                  EVENT_COLOR[e.event_type] ?? "border-l-gray-600"
                } hover:bg-gray-800/20 transition-colors`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs text-gray-300 font-medium">
                      {e.event_type}
                    </span>
                    {e.actor_role && (
                      <span className="text-xs text-gray-500 capitalize">
                        by {e.actor_role}
                      </span>
                    )}
                    {e.target_type && (
                      <span className="text-xs text-gray-600">
                        → {e.target_type}
                      </span>
                    )}
                  </div>
                  {e.details && (
                    <p className="text-xs text-gray-600 mt-0.5 truncate">
                      {Object.entries(e.details)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(" · ")}
                    </p>
                  )}
                </div>
                <time className="text-xs text-gray-600 whitespace-nowrap shrink-0">
                  {new Date(e.created_at).toLocaleTimeString()}
                </time>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
