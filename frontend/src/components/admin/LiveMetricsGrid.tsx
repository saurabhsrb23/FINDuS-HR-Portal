"use client";

import { useEffect, useRef, useState } from "react";
import { adminAPI } from "@/lib/adminAPI";
import type { MonitoringMetrics } from "@/types/admin";
import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface DataPoint {
  t: number;
  value: number;
}

interface SparklineCardProps {
  label: string;
  value: string | number;
  data: DataPoint[];
  color?: string;
  unit?: string;
}

function SparklineCard({ label, value, data, color = "#6366f1", unit }: SparklineCardProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-gray-400 text-xs">{label}</p>
          <p className="text-white text-xl font-bold mt-0.5">
            {value}
            {unit && <span className="text-xs text-gray-500 ml-1">{unit}</span>}
          </p>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={48}>
        <LineChart data={data}>
          <Tooltip
            contentStyle={{
              background: "#111827",
              border: "1px solid #374151",
              borderRadius: "8px",
              fontSize: "11px",
              color: "#e5e7eb",
            }}
            formatter={(v: number) => [`${v}${unit ?? ""}`, label]}
            labelFormatter={() => ""}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

const MAX_POINTS = 20;

export function LiveMetricsGrid() {
  const [wsHistory, setWsHistory] = useState<DataPoint[]>([]);
  const [dbHistory, setDbHistory] = useState<DataPoint[]>([]);
  const [redisHitHistory, setRedisHitHistory] = useState<DataPoint[]>([]);
  const [groqHistory, setGroqHistory] = useState<DataPoint[]>([]);
  const [latest, setLatest] = useState<MonitoringMetrics | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function appendPoint(
    setter: React.Dispatch<React.SetStateAction<DataPoint[]>>,
    value: number
  ) {
    setter((prev) => [
      ...prev.slice(-(MAX_POINTS - 1)),
      { t: Date.now(), value },
    ]);
  }

  async function poll() {
    try {
      const m = await adminAPI.getMonitoring();
      setLatest(m);
      appendPoint(setWsHistory, m.active_ws_connections);
      appendPoint(setDbHistory, m.db_latency_ms);
      appendPoint(setRedisHitHistory, m.redis_hit_rate);
      appendPoint(setGroqHistory, m.groq_calls_today);
    } catch {
      // silently ignore polling errors
    }
  }

  useEffect(() => {
    poll();
    intervalRef.current = setInterval(poll, 5000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <section className="space-y-3">
      <h2 className="text-gray-300 font-medium text-sm uppercase tracking-wide">
        Live Metrics (5s poll)
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SparklineCard
          label="WebSocket Connections"
          value={latest?.active_ws_connections ?? 0}
          data={wsHistory}
          color="#22c55e"
        />
        <SparklineCard
          label="DB Latency"
          value={latest?.db_latency_ms.toFixed(1) ?? "—"}
          unit="ms"
          data={dbHistory}
          color="#f59e0b"
        />
        <SparklineCard
          label="Redis Hit Rate"
          value={latest ? `${latest.redis_hit_rate.toFixed(1)}%` : "—"}
          data={redisHitHistory}
          color="#6366f1"
        />
        <SparklineCard
          label="Groq Calls Today"
          value={latest?.groq_calls_today ?? 0}
          data={groqHistory}
          color="#ec4899"
        />
      </div>
    </section>
  );
}
