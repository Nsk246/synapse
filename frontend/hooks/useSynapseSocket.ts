'use client'
import { useEffect, useRef, useCallback } from 'react'
import { useGraphStore } from './useGraphStore'
import type { SynapseEvent } from '@/lib/types'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000/ws/trace'
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export function useSynapseSocket() {
  const wsRef       = useRef<WebSocket | null>(null)
  const pingRef     = useRef<ReturnType<typeof setInterval> | null>(null)
  const processEvent = useGraphStore(s => s.processEvent)
  const resetRun     = useGraphStore(s => s.resetRun)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      console.log('[Synapse] WS connected')
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping')
      }, 20000)
    }

    ws.onmessage = (ev) => {
      try {
        const event: SynapseEvent = JSON.parse(ev.data)
        processEvent(event)
      } catch { /* ignore malformed */ }
    }

    ws.onclose = () => {
      console.log('[Synapse] WS closed — reconnecting in 2s')
      if (pingRef.current) clearInterval(pingRef.current)
      setTimeout(connect, 2000)
    }

    ws.onerror = () => ws.close()
    wsRef.current = ws
  }, [processEvent])

  useEffect(() => {
    connect()
    return () => {
      if (pingRef.current) clearInterval(pingRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  const triggerRun = useCallback(async (query: string, threshold: number) => {
    resetRun()
    const res = await fetch(`${API_URL}/api/run`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ query, threshold }),
    })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    return res.json()
  }, [resetRun])

  const submitOverride = useCallback(async (edgeId: string, reason: string) => {
    await fetch(`${API_URL}/api/override`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ edge_id: edgeId, reason }),
    })
  }, [])

  return { triggerRun, submitOverride }
}
