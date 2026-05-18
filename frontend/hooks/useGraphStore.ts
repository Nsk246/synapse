import { create } from 'zustand'
import type { NodeState, EdgeState, AlertEvent, SynapseEvent, RunState } from '@/lib/types'

interface GraphStore extends RunState {
  setThreshold:      (t: number) => void
  selectEdge:        (id: string | null) => void
  resetRun:          () => void
  processEvent:      (e: SynapseEvent) => void
}

const INITIAL_NODES: Record<string, NodeState> = {
  query_planner:    { id: 'query_planner',    label: 'Query Planner',    status: 'idle' },
  web_researcher:   { id: 'web_researcher',   label: 'Web Researcher',   status: 'idle' },
  evidence_analyst: { id: 'evidence_analyst', label: 'Evidence Analyst', status: 'idle' },
  report_writer:    { id: 'report_writer',    label: 'Report Writer',    status: 'idle' },
}

const INITIAL_EDGES: Record<string, EdgeState> = {
  query_planner_to_web_researcher:      { id: 'query_planner_to_web_researcher',      source: 'query_planner',    target: 'web_researcher',   status: 'idle', drift_history: [] },
  web_researcher_to_evidence_analyst:   { id: 'web_researcher_to_evidence_analyst',   source: 'web_researcher',   target: 'evidence_analyst', status: 'idle', drift_history: [] },
  evidence_analyst_to_report_writer:    { id: 'evidence_analyst_to_report_writer',    source: 'evidence_analyst', target: 'report_writer',    status: 'idle', drift_history: [] },
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  status:           'idle',
  nodes:            { ...INITIAL_NODES },
  edges:            { ...INITIAL_EDGES },
  alerts:           [],
  threshold:        0.85,
  selected_edge_id: null,

  setThreshold: (t) => set({ threshold: t }),
  selectEdge:   (id) => set({ selected_edge_id: id }),

  resetRun: () => set({
    status:           'idle',
    nodes:            { ...INITIAL_NODES },
    edges:            { ...INITIAL_EDGES },
    alerts:           [],
    selected_edge_id: null,
  }),

  processEvent: (e: SynapseEvent) => {
    const s = get()
    const alert = (msg: string, severity: AlertEvent['severity']): AlertEvent => ({
      id:        `${e.type}-${Date.now()}`,
      timestamp: e.timestamp,
      type:      e.type,
      message:   msg,
      severity,
    })

    switch (e.type) {
      case 'node_start':
        if (!e.nodeId) return
        set({
          status: 'running',
          nodes: { ...s.nodes, [e.nodeId]: { ...s.nodes[e.nodeId], status: 'running' } },
          alerts: [...s.alerts, alert(`${s.nodes[e.nodeId]?.label ?? e.nodeId} started`, 'info')],
        })
        break

      case 'node_complete':
        if (!e.nodeId) return
        set({
          nodes: { ...s.nodes, [e.nodeId]: {
            ...s.nodes[e.nodeId],
            status:         'complete',
            duration_ms:    e.duration_ms,
            output_preview: e.output_preview,
            last_run:       e.timestamp,
          }},
        })
        break

      case 'handoff_start':
        if (!e.edgeId) return
        set({
          edges: { ...s.edges, [e.edgeId]: { ...s.edges[e.edgeId], status: 'transmitting' } },
        })
        break

      case 'schema_pass':
        if (!e.edgeId) return
        set({
          edges: { ...s.edges, [e.edgeId]: { ...s.edges[e.edgeId], status: 'schema_pass' } },
        })
        break

      case 'schema_fail':
        if (!e.edgeId) return
        set({
          edges: { ...s.edges, [e.edgeId]: { ...s.edges[e.edgeId], status: 'schema_fail' } },
          alerts: [...s.alerts, alert(`Schema fail on ${e.edgeId}: ${e.error}`, 'error')],
        })
        break

      case 'drift_pass':
        if (!e.edgeId || e.score == null) return
        set({
          edges: { ...s.edges, [e.edgeId]: {
            ...s.edges[e.edgeId],
            status:        'drift_pass',
            drift_score:   e.score,
            threshold:     e.threshold,
            drift_history: [...(s.edges[e.edgeId]?.drift_history ?? []), e.score].slice(-10),
          }},
          alerts: [...s.alerts, alert(`✓ Drift pass ${e.edgeId} (${e.score?.toFixed(3)})`, 'success')],
        })
        break

      case 'drift_fail':
        if (!e.edgeId || e.score == null) return
        set({
          edges: { ...s.edges, [e.edgeId]: {
            ...s.edges[e.edgeId],
            status:             'drift_fail',
            drift_score:        e.score,
            threshold:          e.threshold,
            original_intent:    e.original_intent,
            transformed_output: e.transformed_output,
            drift_history:      [...(s.edges[e.edgeId]?.drift_history ?? []), e.score].slice(-10),
          }},
          alerts: [...s.alerts, alert(`⚠ Drift fail ${e.edgeId} (${e.score?.toFixed(3)} < ${e.threshold})`, 'warning')],
        })
        break

      case 'run_complete':
        set({
          status: e.drift_events && e.drift_events > 0 ? 'error' : 'complete',
          alerts: [...s.alerts, alert(
            `Run complete — ${e.drift_events ?? 0} drift event(s) in ${e.total_duration_ms}ms`,
            e.drift_events && e.drift_events > 0 ? 'warning' : 'success',
          )],
        })
        break
    }
  },
}))
