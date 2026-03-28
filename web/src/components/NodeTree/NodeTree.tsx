import React from 'react'
import type { Node } from '../../types/node'
import NodeTreeItem from './NodeTreeItem'
import { useNodesStore } from '../../store/nodesStore'
import { nodesApi } from '../../api/nodes'

export default function NodeTree() {
  const { nodes, isLoading, error, setNodes, setLoading, setError } = useNodesStore()
  const [expanded, setExpanded] = React.useState<Set<string>>(new Set())

  React.useEffect(() => {
    setLoading(true)
    nodesApi.getAll()
      .then((data: Node[]) => {
        setNodes(data)
        setError(null)
      })
      .catch((err: Error) => {
        setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [setNodes, setLoading, setError])

  const toggleExpand = (name: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  if (isLoading) {
    return (
      <div style={{ padding: '16px', color: '#888', fontSize: '13px' }}>
        Loading nodes...
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '16px', color: '#ff4444', fontSize: '12px' }}>
        Error: {error}
      </div>
    )
  }

  if (nodes.length === 0) {
    return (
      <div style={{ padding: '16px', color: '#666', fontSize: '12px' }}>
        No nodes configured
      </div>
    )
  }

  return (
    <div style={{ padding: '4px 0' }}>
      <div style={{
        padding: '6px 12px',
        fontSize: '11px',
        color: '#888',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        borderBottom: '1px solid #222',
        marginBottom: '4px',
      }}>
        Nodes ({nodes.length})
      </div>
      {nodes.map((node: Node) => (
        <NodeTreeItem
          key={node.name}
          node={node}
          expanded={expanded.has(node.name)}
          onToggle={() => toggleExpand(node.name)}
        />
      ))}
    </div>
  )
}