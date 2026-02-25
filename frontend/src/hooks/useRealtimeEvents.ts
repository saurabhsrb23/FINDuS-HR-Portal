/**
 * useRealtimeEvents — WebSocket hook for Module 7 real-time events.
 *
 * Connects to the backend WebSocket endpoint (/ws?token=JWT) on mount.
 * Auto-reconnects with exponential back-off (1 s → 2 s → 4 s → … → 30 s max).
 * Exposes:
 *   - `status` — "connecting" | "connected" | "disconnected"
 *   - `lastEvent` — the most recent WS event received
 *   - `events` — ring buffer of the last 50 events (newest first)
 *   - `subscribe(eventType, handler)` — register a per-event-type callback
 *   - `unsubscribe(eventType, handler)` — de-register a callback
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getToken } from "@/lib/auth";

// ── Types ─────────────────────────────────────────────────────────────────────

export type WSStatus = "connecting" | "connected" | "disconnected";

export interface RealtimeEvent {
  event_type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

type EventHandler = (event: RealtimeEvent) => void;

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8001";

const MAX_EVENTS = 50;
const MAX_BACKOFF_MS = 30_000;

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useRealtimeEvents() {
  const [status, setStatus] = useState<WSStatus>("disconnected");
  const [events, setEvents] = useState<RealtimeEvent[]>([]);
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelayRef = useRef(1_000);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);
  const listenersRef = useRef<Map<string, Set<EventHandler>>>(new Map());

  const subscribe = useCallback((eventType: string, handler: EventHandler) => {
    if (!listenersRef.current.has(eventType)) {
      listenersRef.current.set(eventType, new Set());
    }
    listenersRef.current.get(eventType)!.add(handler);
  }, []);

  const unsubscribe = useCallback((eventType: string, handler: EventHandler) => {
    listenersRef.current.get(eventType)?.delete(handler);
  }, []);

  const connect = useCallback(() => {
    if (unmountedRef.current) return;
    const token = getToken();
    if (!token) return; // Not authenticated yet — skip

    setStatus("connecting");
    const url = `${WS_BASE_URL}/ws?token=${encodeURIComponent(token)}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (unmountedRef.current) {
        ws.close();
        return;
      }
      setStatus("connected");
      reconnectDelayRef.current = 1_000; // reset back-off on success
    };

    ws.onmessage = (msgEvent) => {
      try {
        const data = JSON.parse(msgEvent.data) as RealtimeEvent;

        // Ignore internal ping/pong
        if (data.event_type === "ping") return;

        setLastEvent(data);
        setEvents((prev) => [data, ...prev].slice(0, MAX_EVENTS));

        // Dispatch to registered per-type listeners
        listenersRef.current.get(data.event_type)?.forEach((fn) => fn(data));
        // Also dispatch to wildcard listeners
        listenersRef.current.get("*")?.forEach((fn) => fn(data));
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = (evt) => {
      wsRef.current = null;
      if (unmountedRef.current) return;
      setStatus("disconnected");

      // Don't reconnect on auth failure (4001)
      if (evt.code === 4001) {
        return;
      }

      // Exponential back-off reconnect
      reconnectTimerRef.current = setTimeout(() => {
        reconnectDelayRef.current = Math.min(
          reconnectDelayRef.current * 2,
          MAX_BACKOFF_MS
        );
        connect();
      }, reconnectDelayRef.current);
    };

    ws.onerror = () => {
      // onerror is always followed by onclose — handled there
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    unmountedRef.current = false;
    connect();
    return () => {
      unmountedRef.current = true;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close(1000, "component unmounted");
    };
  }, [connect]);

  return { status, events, lastEvent, subscribe, unsubscribe };
}

// ── Shared singleton context (optional convenience) ───────────────────────────

import { createContext, useContext } from "react";

export interface RealtimeContextValue {
  status: WSStatus;
  events: RealtimeEvent[];
  lastEvent: RealtimeEvent | null;
  subscribe: (eventType: string, handler: EventHandler) => void;
  unsubscribe: (eventType: string, handler: EventHandler) => void;
}

export const RealtimeContext = createContext<RealtimeContextValue>({
  status: "disconnected",
  events: [],
  lastEvent: null,
  subscribe: () => {},
  unsubscribe: () => {},
});

export function useRealtime() {
  return useContext(RealtimeContext);
}
