import React from 'react'
import type { Node, NodeToken } from '../../types/node'
import { useNodesStore } from '../../store/nodesStore'

interface Props {
  node: Node
  expanded: boolean
  onToggle: () => void
}

const statusColor: Record<string, string> = {
  online: '#44ff88',
  offline: '#ff4444',
  scanning: '#ffcc00',
  error: '#ff8844',
}

const tokenTypeColor: Record<string, string> = {
  FBC: '#7b5ea7',
  RPC: '#4a8fc7',
  LOG: '#4ab577',
  LIS: '#c7a04a',
}

export default function NodeTreeItem({ node, expanded, onToggle }: Props) {
  const { selectedNode, setSelectedNode } = useNodesStore()
  const isSelected = selectedNode?.name === node.name
  const color = statusColor[node.status] ?? '#888'

  const handleSelect = () => {
    setSelectedNode(node)
  }

  return (
    <div>
      <div
        onClick={() => { handleSelect(); onToggle() }}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 12px',
          cursor: 'pointer',
          backgroundColor: isSelected ? '#2a1f3d' : 'transparent',
          borderLeft: isSelected ? '2px solid #5D3E8E' : '2px solid transparent',
          transition: 'background 0.15s',
          userSelect: 'none',
        }}
        onMouseEnter={(e) => {
          if (!isSelected) (e.currentTarget as HTMLDivElement).style.backgroundColor = '#1f1f1f'
        }}
        onMouseLeave={(e) => {
          if (!isSelected) (e.currentTarget as HTMLDivElement).style.backgroundColor = 'transparent'
        }}
      >
        {/* Expand arrow */}
        <span style={{ color: '#666', fontSize: '10px', width: '10px', flexShrink: 0 }}>
          {node.tokens.length > 0 ? (expanded ? '▼' : '▶') : '·'}
        </span>

        {/* Status dot */}
        <span style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: color,
          flexShrink: 0,
          boxShadow: `0 0 4px ${color}66`,
        }} />

        {/* Node info */}
        <span style={{ flex: 1, fontSize: '13px', color: '#ddd' }}>
          {node.name}
        </span>
        <span style={{ fontSize: '11px', color: '#666' }}>
          {node.ip_address}
        </span>
      </div>

      {/* Token list */}
      {expanded && node.tokens.length > 0 && (
        <div style={{ paddingLeft: '32px' }}>
          {node.tokens.map((token: NodeToken) => (
            <div
              key={token.token_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 8px',
                fontSize: '12px',
                color: '#aaa',
              }}
            >
              <span style={{
                fontSize: '10px',
                fontWeight: 'bold',
                color: tokenTypeColor[token.token_type] ?? '#888',
                width: '32px',
                flexShrink: 0,
              }}>
                {token.token_type}
              </span>
              <span style={{ fontFamily: 'monospace', color: '#bbb' }}>
                {token.token_id}
              </span>
              <span style={{ color: '#555', marginLeft: 'auto' }}>
                :{token.port}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}