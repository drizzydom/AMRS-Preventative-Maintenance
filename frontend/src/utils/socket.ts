import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

export const initializeSocket = () => {
  if (socket) return socket

  socket = io(window.location.origin, {
    transports: ['polling', 'websocket'],
    upgrade: true,
    timeout: 30000,
    autoConnect: false,
    reconnection: false,
  })

  socket.on('connect', () => {
    console.log('[SocketIO] Connected to server')
  })

  socket.on('connected', (data: any) => {
    console.log('[SocketIO] Server confirmed:', data?.client_id)
  })

  socket.on('sync', (data: any) => {
    console.log('[SocketIO] Sync event received:', data?.message)
    // Notify application to refresh relevant data
    window.dispatchEvent(new CustomEvent('socket-sync', { detail: data }))
  })

  socket.on('disconnect', (reason: any) => {
    console.log('[SocketIO] Disconnected:', reason)
  })

  socket.on('connect_error', (err: any) => {
    console.error('[SocketIO] Connect error:', err)
  })

  socket.connect()
  return socket
}

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

export const getSocket = () => socket
