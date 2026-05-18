'use client'
import { useCallback, useMemo } from 'react'
import {
  ReactFlow, Background, BackgroundVariant,
  type Node, type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import AgentNode    from './AgentNode'
import SynapseEdge  from './SynapseEdge'
import { useGraphStore } from '@/hooks/useGraphStore'

const nodeTypes = { agentNode: AgentNode }
const edgeTypes = { synapseEdge: SynapseEdge }

const STATIC_NODES: Node[] = [
  { id: 'query_planner',    type: 'agentNode', position: { x: 60,  y: 180 }, data: { label: 'Query Planner',    nodeId: 'query_planner'    } },
  { id: 'web_researcher',   type: 'agentNode', position: { x: 300, y: 180 }, data: { label: 'Web Researcher',   nodeId: 'web_researcher'   } },
  { id: 'evidence_analyst', type: 'agentNode', position: { x: 540, y: 180 }, data: { label: 'Evidence Analyst', nodeId: 'evidence_analyst' } },
  { id: 'report_writer',    type: 'agentNode', position: { x: 780, y: 180 }, data: { label: 'Report Writer',    nodeId: 'report_writer'    } },
]

const STATIC_EDGES: Edge[] = [
  { id: 'query_planner_to_web_researcher',    source: 'query_planner',    target: 'web_researcher',   type: 'synapseEdge', data: { edgeId: 'query_planner_to_web_researcher'    } },
  { id: 'web_researcher_to_evidence_analyst', source: 'web_researcher',   target: 'evidence_analyst', type: 'synapseEdge', data: { edgeId: 'web_researcher_to_evidence_analyst'  } },
  { id: 'evidence_analyst_to_report_writer',  source: 'evidence_analyst', target: 'report_writer',    type: 'synapseEdge', data: { edgeId: 'evidence_analyst_to_report_writer'   } },
]

export default function SynapseCanvas() {
  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={STATIC_NODES}
        edges={STATIC_EDGES}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        colorMode="dark"
        fitView
        fitViewOptions={{ padding: 0.3 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color="#1e1e2e"
        />
      </ReactFlow>
    </div>
  )
}
