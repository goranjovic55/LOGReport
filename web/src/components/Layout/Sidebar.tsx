import NodeTree from '../NodeTree/NodeTree'

export default function Sidebar() {
  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <NodeTree />
    </div>
  )
}