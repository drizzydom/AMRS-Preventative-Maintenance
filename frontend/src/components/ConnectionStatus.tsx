import { useEffect, useState } from 'react'
import { Badge, Tooltip } from 'antd'
import { getSocket } from '../utils/socket'

/**
 * Shows real-time connection status in the header
 */
const ConnectionStatus: React.FC = () => {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const socket = getSocket()
    if (!socket) {
      console.warn('[ConnectionStatus] Socket not initialized')
      return
    }

    // Update connection status
    const updateStatus = () => {
      setConnected(socket.connected)
    }

    // Initial status
    updateStatus()

    // Listen for connection events
    socket.on('connect', () => {
      console.log('[ConnectionStatus] Connected')
      setConnected(true)
    })

    socket.on('disconnect', () => {
      console.log('[ConnectionStatus] Disconnected')
      setConnected(false)
    })

    // Cleanup
    return () => {
      socket.off('connect')
      socket.off('disconnect')
    }
  }, [])

  return (
    <Tooltip title={connected ? 'Real-time sync active' : 'Disconnected from server'}>
      <Badge 
        status={connected ? 'success' : 'error'} 
        text={connected ? 'Connected' : 'Disconnected'}
        style={{ marginLeft: '16px' }}
      />
    </Tooltip>
  )
}

export default ConnectionStatus
