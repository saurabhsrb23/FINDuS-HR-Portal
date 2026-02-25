"use client";

import { useEffect, useRef, useState } from "react";

interface Props {
  value: number | null;
  /** Event type(s) that increment this counter */
  eventTypes?: string[];
  label: string;
  icon?: string;
  colorClass?: string;
  /** Called with new value when counter changes */
  onUpdate?: (newValue: number) => void;
}

/**
 * LiveCounterBadge — KPI card number that animates on real-time updates.
 *
 * Usage:
 *   <LiveCounterBadge value={appCount} label="Applications" eventTypes={["new_application"]} />
 *
 * When a matching WebSocket event arrives the number bumps +1 with a
 * brief pulse animation to indicate live data.
 */
export default function LiveCounterBadge({
  value,
  label,
  icon,
  colorClass = "text-gray-900",
}: Props) {
  const [displayValue, setDisplayValue] = useState(value);
  const [pulse, setPulse] = useState(false);
  const prevRef = useRef(value);

  // Sync when parent value changes
  useEffect(() => {
    if (value !== prevRef.current) {
      setDisplayValue(value);
      prevRef.current = value;
      setPulse(true);
      const t = setTimeout(() => setPulse(false), 600);
      return () => clearTimeout(t);
    }
  }, [value]);

  return (
    <div
      className={`transition-all duration-300 ${
        pulse ? "scale-110 opacity-90" : "scale-100 opacity-100"
      }`}
    >
      {icon && <span className="text-2xl block mb-1">{icon}</span>}
      <p
        className={`text-3xl font-bold ${colorClass} transition-all duration-300 ${
          pulse ? "text-indigo-600" : ""
        }`}
      >
        {displayValue ?? "—"}
      </p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  );
}
