'use client'
import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { useGraphStore } from '@/hooks/useGraphStore'
import type { NodeStatus } from '@/lib/types'
import { clsx } from 'clsx'

const STATUS_COLORS: Record<NodeStatus, string> = {
  idle:     'border-[#1e1e2e] bg-[#16161f]',
  running:  'border-indigo-500 bg-[#16161f] node-running',
  complete: 'border-emerald-500/60 bg-[#16161f]',
  error:    'border-red-500 bg-[#16161f]',
}
const STATUS_DOT: Record<NodeStatus, string> = {
  idle:     'bg-[#3b3b52]',
  running:  'bg-indigo-400 animate-pulse',
  complete: 'bg-emerald-400',
  error:    'bg-red-400',
}
const STATUS_LABEL: Record<NodeStatus, string> = {
  idle:     'idle',
  running:  'running',
  complete: 'done',
  error:    'error',
}

interface AgentNodeData { label: string; nodeId: string }

function AgentNode({ data }: { data: AgentNodeData }) {
  const node = useGraphStore(s => s.nodes[data.nodeId])
  const status: NodeStatus = node?.status ?? 'idle'

  return (
    <div className={clsx(
      'relative w-44 rounded-xl border px-4 py-3 transition-all duration-300 cursor-default select-none',
      STATUS_COLORS[status],
    )}>
      <Handle
        type="target"
        position={Position.Left}
        className="!w-2 !h-2 !bg-[#3b3b52] !border-[#1e1e2e]"
      />

      {/* Status dot */}
      <div className="flex items-center gap-2 mb-1">
        <span className={clsx('w-2 h-2 rounded-full flex-shrink-0', STATUS_DOT[status])} />
        <span className="text-[10px] font-mono text-[#6b6b8a] uppercase tracking-wider">
          {STATUS_LABEL[status]}
        </span>
      </div>

      {/* Node label */}
      <div className="text-sm font-semibold text-[#e2e2f0] leading-tight">
        {data.label}
      </div>

      {/* Duration */}
      {node?.duration_ms && (
        <div className="mt-1 text-[10px] text-[#6b6b8a] font-mono">
          {node.duration_ms}ms
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        className="!w-2 !h-2 !bg-[#3b3b52] !border-[#1e1e2e]"
      />
    </div>
  )
}

export default memo(AgentNode)
