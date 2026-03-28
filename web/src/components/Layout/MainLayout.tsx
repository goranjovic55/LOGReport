import React from 'react'
import Sidebar from './Sidebar'
import TabContainer from '../Tabs/TabContainer'

const styles: Record<string, React.CSSProperties> = {
  layout: {
    display: 'flex',
    width: '100vw',
    height: '100vh',
    backgroundColor: '#1a1a1a',
    color: '#e0e0e0',
    overflow: 'hidden',
  },
  left: {
    width: '300px',
    minWidth: '300px',
    borderRight: '1px solid #333',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#141414',
  },
  right: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    padding: '10px 16px',
    backgroundColor: '#5D3E8E',
    color: '#fff',
    fontWeight: 'bold',
    fontSize: '14px',
    letterSpacing: '1px',
    flexShrink: 0,
  },
}

export default function MainLayout() {
  return (
    <div style={styles.layout}>
      <div style={styles.left}>
        <div style={styles.header}>LOGReport</div>
        <Sidebar />
      </div>
      <div style={styles.right}>
        <TabContainer />
      </div>
    </div>
  )
}