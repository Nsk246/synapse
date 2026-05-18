'use client'
import { useState } from 'react'
import { X, AlertTriangle, CheckCircle } from 'lucide-react'
import { useGraphStore } from '@/hooks/useGraphStore'
import { useSynapseSocket } from '@/hooks/useSynapseSocket'

export default function DriftForensics() {
  const selectedId  = useGraphStore(s => s.selected_edge_id)
  const edges       = useGraphStore(s => s.edges)
  const selectEdge  = useGraphStore(s => s.selectEdge)
  const { submitOverride } = useSynapseSocket()
  const [reason, setReason] = useState('')
  const [overridden, setOverridden] = useState(false)

  if (!selectedId) return null
  const edge = edges[selectedId]
  if (!edge) return null

  const score = edge.drift_score ?? 0
  const tau   = edge.threshold   ?? 0.85
  const pct   = Math.max(0, Math.min(100, (score / 1) * 100))
  const tauPct = tau * 100

  const handleOverride = async () => {
    if (!reason.trim()) return
    await submitOverride(selectedId, reason)
    setOverridden(true)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm fade-in">
      <div className="relative w-[680px] max-h-[85vh] overflow-y-auto rounded-2xl border border-[#1e1e2e] bg-[#111118] shadow-2xl">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1e1e2e]">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <div>
              <h2 className="text-sm font-semibold text-[#e2e2f0]">Drift Forensics</h2>
              <p className="text-xs text-[#6b6b8a] font-mono">{selectedId}</p>
            </div>
          </div>
          <button
            onClick={() => { selectEdge(null); setOverridden(false); setReason('') }}
            className="text-[#6b6b8a] hover:text-[#e2e2f0] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">

          {/* Score gauge */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-[#6b6b8a] uppercase tracking-wider font-mono">
                Cosine similarity
              </span>
              <span className="text-xs font-mono text-amber-400 font-semibold">
                {score.toFixed(4)} / τ={tau}
              </span>
            </div>
            <div className="relative h-3 rounded-full bg-[#1e1e2e] overflow-hidden">
              {/* Score bar */}
              <div
                className="absolute top-0 left-0 h-full rounded-full bg-amber-500 transition-all duration-700"
                style={{ width: `${pct}%` }}
              />
              {/* Threshold marker */}
              <div
                className="absolute top-0 h-full w-0.5 bg-white/40"
                style={{ left: `${tauPct}%` }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-[#6b6b8a] font-mono">0.0</span>
              <span
                className="text-[10px] text-white/40 font-mono"
                style={{ marginLeft: `${tauPct - 5}%` }}
              >τ</span>
              <span className="text-[10px] text-[#6b6b8a] font-mono">1.0</span>
            </div>
          </div>

          {/* Diff: intent vs output */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-[#1e1e2e] p-4">
              <div className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider mb-2">
                Contract intent
              </div>
              <p className="text-xs text-[#e2e2f0] leading-relaxed">
                {edge.original_intent ?? '—'}
              </p>
            </div>
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
              <div className="text-[10px] font-mono text-amber-400 uppercase tracking-wider mb-2">
                Agent output
              </div>
              <p className="text-xs text-[#e2e2f0] leading-relaxed line-clamp-6">
                {edge.transformed_output ?? '—'}
              </p>
            </div>
          </div>

          {/* Drift history sparkline */}
          {edge.drift_history.length > 1 && (
            <div>
              <div className="text-[10px] font-mono text-[#6b6b8a] uppercase tracking-wider mb-2">
                Drift history (last {edge.drift_history.length} runs)
              </div>
              <div className="flex items-end gap-1 h-8">
                {edge.drift_history.map((v, i) => (
                  <div
                    key={i}
                    className="flex-1 rounded-sm transition-all"
                    style={{
                      height:      `${Math.max(4, v * 100)}%`,
                      background:  v >= tau ? '#22c55e' : '#f59e0b',
                      opacity:     0.7,
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Override panel */}
          {!overridden ? (
            <div className="rounded-xl border border-[#1e1e2e] p-4 space-y-3">
              <div className="text-[10px] font-mono text-[#6b6b8a] uppercase tracking-wider">
                Human override
              </div>
              <input
                type="text"
                placeholder="Reason for accepting this drift..."
                value={reason}
                onChange={e => setReason(e.target.value)}
                className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm text-[#e2e2f0] placeholder-[#3b3b52] focus:outline-none focus:border-indigo-500/60 transition-colors"
              />
              <button
                onClick={handleOverride}
                disabled={!reason.trim()}
                className="w-full py-2 rounded-lg text-sm font-medium transition-all
                  bg-amber-500/10 border border-amber-500/40 text-amber-300
                  hover:bg-amber-500/20 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Accept drift — allow pipeline to continue
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
              <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span className="text-sm text-emerald-300">Override accepted. Decision logged.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
