"use client";
import { useEffect, useRef, useCallback } from "react";
import { useNotifStore } from "@/lib/store";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
const RECONNECT_DELAY = 3000;

export function useWebSocket(userId: string | null | undefined) {
    const ws = useRef<WebSocket | null>(null);
    const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const increment = useNotifStore((s) => s.increment);

    const connect = useCallback(() => {
        if (!userId) return;
        const token =
            typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
        if (!token) return;

        ws.current = new WebSocket(`${WS_URL}/ws/notifications/${userId}?token=${token}`);

        ws.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "notification") {
                    increment();
                }
            } catch {
                // ignore malformed frames
            }
        };

        ws.current.onclose = () => {
            // Auto-reconnect
            reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
        };

        ws.current.onerror = () => {
            ws.current?.close();
        };
    }, [userId, increment]);

    useEffect(() => {
        connect();
        return () => {
            reconnectTimer.current && clearTimeout(reconnectTimer.current);
            ws.current?.close();
        };
    }, [connect]);
}
