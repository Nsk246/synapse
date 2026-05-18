'use client'
import { useState } from 'react'
import { Play, RotateCcw, Activity, AlertTriangle, CheckCircle, Info } from 'lucide-react'
import { useGraphStore } from '@/hooks/useGraphStore'
import { useSynapseSocket } from '@/hooks/useSynapseSocket'
import { clsx } from 'clsx'

const SEVERITY_ICON = {
  info:    <Info    className="w-3 h-3 text-indigo-400 flex-shrink-0" />,
  success: <CheckCircle className="w-3 h-3 text-emerald-400 flex-shrink-0" />,
  warning: <AlertTriangle className="w-3 h-3 text-amber-400 flex-shrink-0" />,
  error:   <AlertTriangle className="w-3 h-3 text-red-400 flex-shrink-0" />,
}

export default function AnatomyPanel() {
  const [query, setQuery]   = useState('What is the impact of sleep deprivation on memory and cognitive performance in adults?')
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState<string | null>(null)

  const { triggerRun } = useSynapseSocket()
  const nodes     = useGraphStore(s => s.nodes)
  const edges     = useGraphStore(s => s.edges)
  const alerts    = useGraphStore(s => s.alerts)
  const threshold = useGraphStore(s => s.threshold)
  const runStatus = useGraphStore(s => s.status)
  const setThreshold = useGraphStore(s => s.setThreshold)
  const resetRun     = useGraphStore(s => s.resetRun)

  const handleRun = async () => {
    if (!query.trim() || loading) return
    setError(null)
    setLoading(true)
    try {
      await triggerRun(query.trim(), threshold)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const recentAlerts = [...alerts].reverse().slice(0, 20)

  return (
    <div className="flex flex-col h-full bg-[#111118] border-r border-[#1e1e2e] overflow-y-auto">

      {/* Header */}
      <div className="px-5 py-4 border-b border-[#1e1e2e]">
        <div className="flex items-center gap-2 mb-1">
          <Activity className="w-4 h-4 text-indigo-400" />
          <h1 className="text-sm font-semibold text-[#e2e2f0] tracking-tight">Synapse</h1>
          <span className={clsx(
            'ml-auto text-[9px] font-mono px-2 py-0.5 rounded-full border',
            runStatus === 'running'  ? 'border-indigo-500/60 text-indigo-400 bg-indigo-500/10' :
            runStatus === 'complete' ? 'border-emerald-500/60 text-emerald-400 bg-emerald-500/10' :
            runStatus === 'error'    ? 'border-amber-500/60 text-amber-400 bg-amber-500/10' :
            'border-[#1e1e2e] text-[#6b6b8a]'
          )}>
            {runStatus}
          </span>
        </div>
        <p className="text-[10px] text-[#6b6b8a]">Semantic drift detector</p>
      </div>

      {/* Query input */}
      <div className="px-5 py-4 border-b border-[#1e1e2e] space-y-3">
        <label className="text-[10px] font-mono text-[#6b6b8a] uppercase tracking-wider">
          Research query
        </label>
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          rows={3}
          className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-xs text-[#e2e2f0] placeholder-[#3b3b52] focus:outline-none focus:border-indigo-500/60 resize-none transition-colors"
          placeholder="Enter a research query..."
        />

        {/* Threshold slider */}
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-[10px] font-mono text-[#6b6b8a]">τ threshold</span>
            <span className="text-[10px] font-mono text-indigo-400">{threshold.toFixed(2)}</span>
          </div>
          <input
            type="range" min={0.5} max={0.99} step={0.01}
            value={threshold}
            onChange={e => setThreshold(parseFloat(e.target.value))}
            className="w-full accent-indigo-500 h-1"
          />
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleRun}
            disabled={loading || runStatus === 'running'}
            className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium
              bg-indigo-500/10 border border-indigo-500/40 text-indigo-300
              hover:bg-indigo-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            <Play className="w-3 h-3" />
            {loading ? 'Running...' : 'Run pipeline'}
          </button>
          <button
            onClick={resetRun}
            className="px-3 py-2 rounded-lg border border-[#1e1e2e] text-[#6b6b8a]
              hover:text-[#e2e2f0] hover:border-[#3b3b52] transition-all"
          >
            <RotateCcw className="w-3 h-3" />
          </button>
        </div>

        {error && (
          <p className="text-xs text-red-400 font-mono">{error}</p>
        )}
      </div>

      {/* Node heartbeats */}
      <div className="px-5 py-4 border-b border-[#1e1e2e]">
        <div className="text-[10px] font-mono text-[#6b6b8a] uppercase tracking-wider mb-3">
          Node status
        </div>
        <div className="space-y-2">
          {Object.values(nodes).map(node => (
            <div key={node.id} className="flex items-center gap-2 py-1.5 px-3 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e]">
              <span className={clsx(
                'w-1.5 h-1.5 rounded-full flex-shrink-0',
                node.status === 'idle'     ? 'bg-[#3b3b52]' :
                node.status === 'running'  ? 'bg-indigo-400 animate-pulse' :
                node.status === 'complete' ? 'bg-emerald-400' : 'bg-red-400'
              )} />
              <span className="text-xs text-[#e2e2f0] flex-1 truncate">{node.label}</span>
              {node.duration_ms && (
                <span className="text-[10px] font-mono text-[#6b6b8a]">{node.duration_ms}ms</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Edge drift scores */}
      <div className="px-5 py-4 border-b border-[#1e1e2e]">
        <div className="text-[10px] font-mono text-[#6b6b8a] uppercase tracking-wider mb-3">
          Handoff scores
        </div>
        <div className="space-y-2">
          {Object.values(edges).map(edge => (
            <div key={edge.id} className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-[#6b6b8a] truncate max-w-[140px]">
                  {edge.id.replace(/_to_/g, ' → ').replace(/_/g, ' ')}
                </span>
                {edge.drift_score != null && (
                  <span className={clsx(
                    'text-[10px] font-mono font-semibold',
                    edge.status === 'drift_pass' ? 'text-emerald-400' : 'text-amber-400'
                  )}>
                    {edge.drift_score.toFixed(3)}
                  </span>
                )}
              </div>
              {/* Mini sparkline */}
              {edge.drift_history.length > 0 && (
                <div className="flex items-end gap-0.5 h-4">
                  {edge.drift_history.map((v, i) => (
                    <div
                      key={i}
                      className="flex-1 rounded-sm"
                      style={{
                        height:     `${Math.max(10, v * 100)}%`,
                        background: v >= (edge.threshold ?? 0.85) ? '#22c55e88' : '#f59e0b88',
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Alert feed */}
      <div className="px-5 py-4 flex-1">
        <div className="text-[10px] font-mono text-[#6b6b8a] uppercase tracking-wider mb-3">
          Event feed
        </div>
        <div className="space-y-1.5 max-h-64 overflow-y-auto">
          {recentAlerts.length === 0 ? (
            <p className="text-[10px] text-[#3b3b52] font-mono">No events yet</p>
          ) : (
            recentAlerts.map(a => (
              <div key={a.id} className="flex items-start gap-2 fade-in">
                {SEVERITY_ICON[a.severity]}
                <span className="text-[10px] text-[#6b6b8a] leading-relaxed">{a.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
