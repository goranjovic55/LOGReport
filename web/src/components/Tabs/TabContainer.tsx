import React from 'react'
import LogProcessorTab from './LogProcessorTab'
import CommanderTab from './CommanderTab'
import TelnetTab from './TelnetTab'
import BsToolTab from './BsToolTab'
import ScanTab from './ScanTab'
import SessionTab from './SessionTab'

type TabId = 'log' | 'commander' | 'telnet' | 'bstool' | 'scan' | 'sessions'

const tabs: { id: TabId; label: string }[] = [
  { id: 'log', label: 'Log Processor' },
  { id: 'commander', label: 'Commander' },
  { id: 'telnet', label: 'Telnet' },
  { id: 'bstool', label: 'BsTool' },
  { id: 'scan', label: 'Scan' },
  { id: 'sessions', label: 'Sessions' },
]

export default function TabContainer() {
  const [active, setActive] = React.useState<TabId>('log')

  const renderTab = () => {
    switch (active) {
      case 'log': return <LogProcessorTab />
      case 'commander': return <CommanderTab />
      case 'telnet': return <TelnetTab />
      case 'bstool': return <BsToolTab />
      case 'scan': return <ScanTab />
      case 'sessions': return <SessionTab />
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab bar */}
      <div style={{
        display: 'flex',
        backgroundColor: '#141414',
        borderBottom: '1px solid #333',
        flexShrink: 0,
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActive(tab.id)}
            style={{
              padding: '8px 16px',
              fontSize: '12px',
              cursor: 'pointer',
              border: 'none',
              borderBottom: active === tab.id ? '2px solid #5D3E8E' : '2px solid transparent',
              backgroundColor: active === tab.id ? '#1f1535' : 'transparent',
              color: active === tab.id ? '#c8a8ff' : '#888',
              transition: 'all 0.15s',
              outline: 'none',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
        {renderTab()}
      </div>
    </div>
  )
}