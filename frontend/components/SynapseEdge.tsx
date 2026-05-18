'use client'
import { memo, useCallback } from 'react'
import { BaseEdge, getSmoothStepPath, EdgeLabelRenderer } from '@xyflow/react'
import { useGraphStore } from '@/hooks/useGraphStore'
import type { EdgeStatus } from '@/lib/types'

const EDGE_COLORS: Record<EdgeStatus, string> = {
  idle:        '#1e1e2e',
  transmitting:'#6366f1',
  schema_pass: '#6366f1',
  drift_pass:  '#22c55e',
  drift_fail:  '#f59e0b',
  schema_fail: '#ef4444',
}

interface SynapseEdgeProps {
  id: string; sourceX: number; sourceY: number
  targetX: number; targetY: number
  sourcePosition: any; targetPosition: any
  data?: { edgeId: string }
}

function SynapseEdge({
  id, sourceX, sourceY, targetX, targetY,
  sourcePosition, targetPosition, data,
}: SynapseEdgeProps) {
  const edgeId     = data?.edgeId ?? id
  const edge       = useGraphStore(s => s.edges[edgeId])
  const selectEdge = useGraphStore(s => s.selectEdge)
  const status: EdgeStatus = edge?.status ?? 'idle'
  const color = EDGE_COLORS[status]
  const isTransmitting = status === 'transmitting' || status === 'schema_pass'
  const isDriftFail    = status === 'drift_fail'
  const isClickable    = status === 'drift_fail' || status === 'schema_fail'

  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX, sourceY, sourcePosition,
    targetX, targetY, targetPosition,
  })

  const handleClick = useCallback(() => {
    if (isClickable) selectEdge(edgeId)
  }, [isClickable, selectEdge, edgeId])

  return (
    <>
      {/* Glow layer for drift_fail */}
      {isDriftFail && (
        <path
          d={edgePath}
          fill="none"
          stroke="#f59e0b"
          strokeWidth={8}
          strokeOpacity={0.15}
          className="node-drifting"
        />
      )}

      {/* Main edge */}
      <BaseEdge
        path={edgePath}
        style={{
          stroke:      color,
          strokeWidth: status === 'idle' ? 1.5 : 2,
          strokeDasharray: isTransmitting ? '6 3' : undefined,
          animation:   isTransmitting
            ? 'particle-flow 0.6s linear infinite'
            : undefined,
          cursor: isClickable ? 'pointer' : 'default',
          transition: 'stroke 0.3s ease',
        }}
        onClick={isClickable ? handleClick : undefined}
      />

      {/* Score badge */}
      {edge?.drift_score != null && (
        <EdgeLabelRenderer>
          <div
            style={{ transform: `translate(-50%,-50%) translate(${labelX}px,${labelY}px)` }}
            className={`absolute pointer-events-${isClickable ? 'auto' : 'none'} nopan`}
            onClick={isClickable ? handleClick : undefined}
          >
            <div className={`
              px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold
              border cursor-${isClickable ? 'pointer' : 'default'}
              transition-all duration-300
              ${isDriftFail
                ? 'bg-amber-500/20 border-amber-500/60 text-amber-300 node-drifting'
                : 'bg-emerald-500/20 border-emerald-500/60 text-emerald-300'}
            `}>
              {isDriftFail ? '⚠ ' : '✓ '}
              {edge.drift_score.toFixed(3)}
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  )
}

export default memo(SynapseEdge)
