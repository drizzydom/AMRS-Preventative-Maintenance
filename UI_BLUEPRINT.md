# AMRS Preventative Maintenance - Complete UI Migration Blueprint

## Executive Summary

This document provides a comprehensive analysis of the legacy HTML/CSS/JavaScript frontend and a complete blueprint for migrating all features to the new React + TypeScript + Ant Design frontend. This document is designed to be used by GitHub Copilot Coding Agent to implement all remaining features in a cohesive, single-session workflow.

**Current Status**: Authentication and basic CRUD pages (Sites, Machines, Audits, Users) are working with real data. Dashboard shows dummy data and needs to be wired to the API. Legacy features like SocketIO real-time sync, desktop UX polish, and advanced UI features need implementation.

---

## Table of Contents

1. [Technology Stack & Architecture](#1-technology-stack--architecture)
2. [Legacy Frontend Analysis](#2-legacy-frontend-analysis)
3. [React Frontend Current State](#3-react-frontend-current-state)
4. [Feature Mapping: Legacy → React](#4-feature-mapping-legacy--react)
5. [Dashboard Fix (PRIORITY)](#5-dashboard-fix-priority)
6. [SocketIO Real-Time Integration](#6-socketio-real-time-integration)
7. [Desktop App UX Requirements](#7-desktop-app-ux-requirements)
8. [UI/UX Features to Implement](#8-uiux-features-to-implement)
9. [API Contract Reference](#9-api-contract-reference)
10. [Implementation Checklist](#10-implementation-checklist)

---

## 1. Technology Stack & Architecture

### Current Stack

**Backend (Flask)**
- Flask 3.0.0 + Flask-SocketIO for real-time sync
- SQLite database with SQLAlchemy ORM
- Session-based authentication with Flask-Login
- API endpoints at `/api/v1/*`
- Serves React frontend from same origin (`http://127.0.0.1:10000/`)

**Frontend (React - NEW)**
- React 18.2.0 + TypeScript 5.2.2
- Ant Design 5.12.0 (UI component library)
- Axios for HTTP requests
- React Router for navigation
- Built to `frontend/dist/`

**Desktop Wrapper (Electron)**
- Electron 28.3.3
- Loads React from Flask at `http://127.0.0.1:10000/`
- Spawns Flask backend automatically on port 10000
- Main process in `main.js`

**Legacy Stack (DEPRECATED - to migrate from)**
- Jinja2 templates (138 HTML files in `/templates/`)
- Vanilla JavaScript (28 files in `/static/js/`)
- Custom CSS (68 files in `/static/css/`)
- Bootstrap 5.2.3
- SocketIO client for real-time updates

### Database Schema (Verified)

```sql
-- Users & Authentication
users: id, username, email, password_hash, role_id, username_hash, email_hash, remember_token
roles: id, name, description, permissions (comma-separated)

-- Core Entities
sites: id, name, location, contact_email, enable_notifications, notification_threshold
machines: id, name, model, serial_number, site_id, decommissioned, decommissioned_date, decommissioned_by, decommissioned_reason
parts: id, name, description, machine_id, maintenance_frequency, maintenance_unit, last_maintenance, next_maintenance, maintenance_days
maintenance_records: id, machine_id, part_id, user_id, maintenance_type, description, date, performed_by, status, notes, comments

-- Audits
audit_tasks: id, name, description, site_id, created_by, interval, custom_interval_days, color
audit_task_completions: id, audit_task_id, completed_by, completed_at
```

**CRITICAL SCHEMA NOTES**:
- Parts have `next_maintenance` and `last_maintenance` dates (NOT MaintenanceRecord)
- Machines have `decommissioned` boolean (NOT `is_decommissioned`)
- MaintenanceRecords track performed work, no `completed` flag

---

## 2. Legacy Frontend Analysis

### 2.1 Core Pages Overview

| Page | Template | JS File | Key Features |
|------|----------|---------|--------------|
| Dashboard | `templates/dashboard.html` | `static/js/dashboard.js` | Stats cards, site filter, overdue/due-soon tables, machine accordion, toggle parts |
| Sites | `templates/sites.html` | N/A (static) | CRUD operations, maintenance status badges, machine count |
| Machines | `templates/machines.html` | N/A (static) | CRUD operations, site filter, parts count, serial numbers |
| Audits | `templates/audits.html` | N/A (static) | Create tasks, checkoff completion, site grouping, color coding |
| Maintenance | `templates/maintenance.html` | Cascading selects | Record maintenance, site → machine → part filters, multi-part modal |
| Parts | `templates/parts.html` | N/A (static) | CRUD operations, machine filter, maintenance schedule |
| Users (Admin) | `templates/admin_users.html` | N/A (static) | User management, role assignment, permissions |
| Login | `templates/login.html` | N/A (static) | Authentication, remember me, forgot password |

### 2.2 Dashboard Deep Dive

**File**: `templates/dashboard.html` (781 lines)

**Key Features**:
1. **Site Filter Dropdown**: Multi-site users can filter entire dashboard by site
2. **Decommissioned Toggle**: Show/hide decommissioned machines
3. **Quick Action Buttons**: "Record Maintenance Now", "View X Overdue Items"
4. **Stats Cards (4)**: 
   - Overdue (red) - Parts needing maintenance NOW
   - Due Soon (yellow) - Parts due within 7 days
   - Up to Date (green) - All parts current
   - Total Parts (blue) - Total count
5. **Clickable Stats Cards**: Click to scroll to relevant section
6. **Overdue Parts Panel**: Top 3 most overdue, table with part/machine/site/days overdue
7. **Due Soon Parts Panel**: Top 3 upcoming, table with part/machine/site/due date
8. **Site Accordion**: Collapsible sections per site with:
   - Site stats summary (overdue/due-soon badges)
   - Machine list per site
   - Toggle parts button per machine
   - Collapsible parts table per machine (status badges)
9. **Machine Status Indicators**: Dynamic calculation based on part statuses
10. **Mobile-Responsive**: Card-list view for tables on mobile

**JavaScript**: `static/js/dashboard.js` (516 lines)
- `dashboardInit()`: Main initialization
- `storeOriginalStats()`: Cache stats for filtering
- `filterSites(siteId)`: Filter dashboard by site, update counters
- `updateCountersFromSite()`: Recalculate stats for filtered site
- `updateMachineStatuses()`: Calculate machine status from parts
- `toggleAllParts()`: Show/hide all parts across all machines
- `setupPartToggles()`: Individual machine part toggle buttons

### 2.3 SocketIO Real-Time Sync

**File**: `static/js/socket-sync.js` (273 lines)

**Key Features**:
1. **Auto-reconnect with exponential backoff**
2. **Heartbeat to maintain connection**
3. **Sync event handler**: Triggers `window.performIncrementalSync()` or page reload
4. **Connection status UI**: Shows connected/disconnected state
5. **Manual disconnect prevention**: Don't reconnect during sync operations

**Socket Events**:
- `connect`: Connection established
- `connected`: Server confirmation with client_id
- `sync`: Trigger data refresh (from other clients or server)
- `heartbeat`: Keep-alive from server
- `pong`: Response to client ping
- `disconnect`: Handle disconnection and reconnect logic
- `connect_error`: Connection failed, retry with backoff

### 2.4 Common UI/UX Patterns

**From `static/js/app.js` (210 lines)**:
1. **Bootstrap Tooltip Initialization**: Auto-init all `[data-bs-toggle="tooltip"]`
2. **Auto-hide Alerts**: Dismiss after 5 seconds (except `.alert-important`)
3. **Confirmation Dialogs**: `[data-confirm]` attribute with custom message
4. **Form Validation**: Bootstrap validation for `.needs-validation` forms
5. **Mobile Navigation**: Navbar toggler for mobile menu
6. **Dark Mode Toggle**: Persists to localStorage
7. **Sidebar State**: Expanded by default, collapsed state saved to localStorage

**UX Enhancements** (from `static/js/ux-enhancements.js`):
- Smooth scrolling for anchor links
- Focus management for modals
- Keyboard shortcuts (Alt+S for search, Alt+N for new, etc.)
- Loading states for buttons
- Table scroll hints for mobile
- Print-friendly layouts

### 2.5 CSS Architecture

**Theme**: `static/css/amrs-theme.css`
- Custom color palette (primary: #005cbf, danger: #d9534f, etc.)
- Dark mode support with `[data-theme="dark"]`
- Component theming (cards, buttons, badges, tables)

**Responsive**: `static/css/responsive-enhancements.css`
- Breakpoints: mobile (<768px), tablet (768-991px), desktop (>992px)
- Hide columns on mobile (`.hide-sm`)
- Card-list alternative for tables on mobile (`.mobile-table-card`)
- Responsive sidebar (hamburger menu on mobile)

**Print**: `static/css/print.css`
- Hide navigation, sidebar, buttons when printing
- Expand all collapsed content
- Black & white styling
- Page break handling

---

## 3. React Frontend Current State

### 3.1 File Structure

```
frontend/src/
├── App.tsx                    # Main app with routing
├── main.tsx                   # Entry point
├── utils/
│   └── api.ts                # Axios client with withCredentials
├── pages/
│   ├── Dashboard.tsx         # ❌ Shows dummy data, needs API wiring
│   ├── Sites.tsx             # ✅ Working with real data
│   ├── Machines.tsx          # ✅ Working with real data
│   ├── Audits.tsx            # ✅ Working with real data
│   ├── Maintenance.tsx       # ⚠️ Partially working, may need updates
│   ├── Users.tsx             # ✅ Working with real data (admin only)
│   └── Login.tsx             # ✅ Working
├── components/
│   ├── Layout.tsx            # Main layout with sidebar/header
│   ├── sites/                # Site CRUD modals
│   ├── machines/             # Machine CRUD modals
│   ├── audits/               # Audit CRUD modals
│   └── users/                # User CRUD modals
└── styles/
    ├── dashboard.css         # Dashboard-specific styles
    └── [other CSS files]
```

### 3.2 Working Pages

**Sites.tsx**: Full CRUD with modals, real API calls, status badges, machine count
**Machines.tsx**: Full CRUD with modals, real API calls, site filter, parts count
**Audits.tsx**: Full CRUD with modals, real API calls, completion tracking
**Users.tsx**: Full CRUD with modals, real API calls, role management

### 3.3 Broken/Incomplete Pages

**Dashboard.tsx** (CRITICAL):
- Shows dummy data: `recentTasksData` hardcoded
- Stats fetch from API but limited fields
- Missing: Overdue/due-soon tables, site filter, machine accordion
- Missing: Real-time updates via SocketIO

**Maintenance.tsx** (NEEDS REVIEW):
- May have cascading select logic issues
- May not match legacy multi-part modal functionality
- Backend API fixed, frontend may need updates

---

## 4. Feature Mapping: Legacy → React

### 4.1 Dashboard Features

| Legacy Feature | Implementation Status | React Component Needed | Priority |
|----------------|----------------------|------------------------|----------|
| **Stats Cards (4)** | ⚠️ Partial (limited API fields) | Update Dashboard.tsx to fetch full API | HIGH |
| **Site Filter Dropdown** | ❌ Missing | Add `<Select>` with site options, filter logic | HIGH |
| **Decommissioned Toggle** | ❌ Missing | Add `<Switch>` to show/hide decommissioned machines | MEDIUM |
| **Quick Action Buttons** | ❌ Missing | Add `<Button>` links to Maintenance page | MEDIUM |
| **Clickable Stats Cards** | ❌ Missing | Add `onClick` handlers to scroll to sections | LOW |
| **Overdue Parts Table** | ❌ Missing | Fetch from `/api/v1/maintenance?status=overdue`, render `<Table>` | HIGH |
| **Due Soon Parts Table** | ❌ Missing | Fetch from `/api/v1/maintenance?status=due_soon`, render `<Table>` | HIGH |
| **Site Accordion** | ❌ Missing | Use Ant Design `<Collapse>` with nested tables | HIGH |
| **Machine List per Site** | ❌ Missing | Fetch machines grouped by site, render in accordion | HIGH |
| **Toggle Parts Button** | ❌ Missing | Add collapsible parts table per machine | MEDIUM |
| **Machine Status Indicators** | ❌ Missing | Calculate from part statuses (overdue/due-soon/ok) | MEDIUM |
| **Mobile-Responsive Cards** | ❌ Missing | Use Ant Design responsive grid and cards | LOW |

### 4.2 SocketIO Features

| Legacy Feature | Implementation Status | React Implementation | Priority |
|----------------|----------------------|----------------------|----------|
| **Connect on mount** | ❌ Missing | Use `socket.io-client` in `useEffect` | HIGH |
| **Sync event handler** | ❌ Missing | Listen to `sync` event, trigger data refresh | HIGH |
| **Heartbeat keep-alive** | ❌ Missing | Implement ping/pong with server | MEDIUM |
| **Auto-reconnect** | ❌ Missing | Handle `disconnect` event, retry with backoff | MEDIUM |
| **Connection status UI** | ❌ Missing | Show badge in header (connected/disconnected) | LOW |

### 4.3 Desktop UX Features

| Legacy Feature | Implementation Status | React Implementation | Priority |
|----------------|----------------------|----------------------|----------|
| **Keyboard Shortcuts** | ❌ Missing | Global `keydown` listener, action dispatch | HIGH |
| **Native Menus** | ❌ Missing | Electron `Menu.buildFromTemplate()` in `main.js` | HIGH |
| **Native Notifications** | ❌ Missing | Electron `Notification` API for overdue alerts | MEDIUM |
| **Print Support** | ⚠️ Partial (CSS only) | Add print-specific React components | MEDIUM |
| **Dark Mode Sync** | ❌ Missing | Sync React state with Electron `nativeTheme` | LOW |
| **Window State Persistence** | ❌ Missing | Save window size/position to localStorage | LOW |

---

## 5. Dashboard Fix (PRIORITY)

### 5.1 Current API Response

**Endpoint**: `GET /api/v1/dashboard`

**Response**:
```json
{
  "data": {
    "total_machines": 25,
    "overdue": 8,
    "due_soon": 12,
    "completed": 34
  },
  "message": "Dashboard data retrieved successfully",
  "status": "success"
}
```

### 5.2 Required Changes to Dashboard.tsx

**File**: `frontend/src/pages/Dashboard.tsx`

**Changes Needed**:

1. **Update Interface**:
```typescript
interface DashboardStats {
  total_machines: number
  overdue: number
  due_soon: number
  completed: number
}

interface OverdueItem {
  id: number
  part_name: string
  machine_name: string
  site_name: string
  days_overdue: number
  next_maintenance: string
}

interface DueSoonItem {
  id: number
  part_name: string
  machine_name: string
  site_name: string
  days_until: number
  next_maintenance: string
}
```

2. **Fetch Real Data**:
```typescript
const [stats, setStats] = useState<DashboardStats | null>(null)
const [overdueItems, setOverdueItems] = useState<OverdueItem[]>([])
const [dueSoonItems, setDueSoonItems] = useState<DueSoonItem[]>([])
const [loading, setLoading] = useState(true)

const fetchDashboardData = async () => {
  try {
    setLoading(true)
    // Fetch stats
    const statsResponse = await apiClient.get('/api/v1/dashboard')
    setStats(statsResponse.data.data)
    
    // Fetch overdue items
    const overdueResponse = await apiClient.get('/api/v1/maintenance?status=overdue')
    setOverdueItems(overdueResponse.data.data)
    
    // Fetch due soon items
    const dueSoonResponse = await apiClient.get('/api/v1/maintenance?status=due_soon')
    setDueSoonItems(dueSoonResponse.data.data)
  } catch (error: any) {
    console.error('Failed to load dashboard data:', error)
    message.error('Failed to load dashboard data')
  } finally {
    setLoading(false)
  }
}
```

3. **Update Stats Cards**:
```typescript
const statsData = stats ? [
  { title: 'Total Machines', value: stats.total_machines, icon: <ToolOutlined />, color: '#1890ff' },
  { title: 'Overdue', value: stats.overdue, icon: <WarningOutlined />, color: '#ff4d4f' },
  { title: 'Due Soon', value: stats.due_soon, icon: <ClockCircleOutlined />, color: '#faad14' },
  { title: 'Completed (This Month)', value: stats.completed, icon: <CheckCircleOutlined />, color: '#52c41a' },
] : []
```

4. **Replace Dummy Table with Real Data**:
```typescript
// Remove hardcoded recentTasksData array

// Add two separate tables for Overdue and Due Soon
<Card title="Overdue Maintenance" className="mb-4">
  <Table
    columns={[
      { title: 'Part', dataIndex: 'part_name', key: 'part_name' },
      { title: 'Machine', dataIndex: 'machine_name', key: 'machine_name' },
      { title: 'Site', dataIndex: 'site_name', key: 'site_name' },
      { title: 'Days Overdue', dataIndex: 'days_overdue', key: 'days_overdue', 
        render: (days) => <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>{days} days</span> },
      { title: 'Next Maintenance', dataIndex: 'next_maintenance', key: 'next_maintenance' },
    ]}
    dataSource={overdueItems}
    rowKey="id"
    pagination={{ pageSize: 10 }}
  />
</Card>

<Card title="Due Soon" className="mb-4">
  <Table
    columns={[
      { title: 'Part', dataIndex: 'part_name', key: 'part_name' },
      { title: 'Machine', dataIndex: 'machine_name', key: 'machine_name' },
      { title: 'Site', dataIndex: 'site_name', key: 'site_name' },
      { title: 'Due In', dataIndex: 'days_until', key: 'days_until',
        render: (days) => <span style={{ color: '#faad14' }}>{days} days</span> },
      { title: 'Next Maintenance', dataIndex: 'next_maintenance', key: 'next_maintenance' },
    ]}
    dataSource={dueSoonItems}
    rowKey="id"
    pagination={{ pageSize: 10 }}
  />
</Card>
```

### 5.3 Additional Dashboard Features (Lower Priority)

1. **Site Filter**: Add `<Select>` dropdown to filter all data by site
2. **Site Accordion**: Use `<Collapse>` to group machines by site
3. **Machine Parts Toggle**: Collapsible parts table per machine
4. **Quick Actions**: Add "Record Maintenance" and "View Overdue" buttons
5. **Mobile Responsive**: Use Ant Design responsive grid (`xs={24} sm={12} md={6}`)

---

## 6. SocketIO Real-Time Integration

### 6.1 Installation

```bash
cd frontend
npm install socket.io-client
```

### 6.2 Implementation Plan

**Create**: `frontend/src/utils/socket.ts`

```typescript
import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

export const initializeSocket = () => {
  if (socket) return socket

  socket = io(window.location.origin, {
    transports: ['polling', 'websocket'],
    upgrade: true,
    timeout: 30000,
    autoConnect: false,
    reconnection: false, // Manual reconnection
    pingTimeout: 120000,
    pingInterval: 60000,
  })

  socket.on('connect', () => {
    console.log('[SocketIO] Connected to server')
  })

  socket.on('connected', (data) => {
    console.log('[SocketIO] Server confirmed:', data.client_id)
  })

  socket.on('sync', (data) => {
    console.log('[SocketIO] Sync event received:', data.message)
    // Trigger global data refresh
    window.dispatchEvent(new CustomEvent('socket-sync'))
  })

  socket.on('disconnect', (reason) => {
    console.log('[SocketIO] Disconnected:', reason)
    // Handle reconnection with exponential backoff
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
```

**Update**: `frontend/src/App.tsx`

```typescript
import { useEffect } from 'react'
import { initializeSocket, disconnectSocket } from './utils/socket'

function App() {
  useEffect(() => {
    // Initialize SocketIO on app mount
    const socket = initializeSocket()

    // Cleanup on unmount
    return () => {
      disconnectSocket()
    }
  }, [])

  // Listen for sync events globally
  useEffect(() => {
    const handleSync = () => {
      console.log('Global sync triggered, refreshing data...')
      // Trigger data refresh in all mounted components
      // Option 1: Use React Context to notify all pages
      // Option 2: Each page listens to this event individually
    }

    window.addEventListener('socket-sync', handleSync)
    return () => window.removeEventListener('socket-sync', handleSync)
  }, [])

  return (
    // ... existing app structure
  )
}
```

**Update**: Each data-fetching page (Dashboard, Sites, Machines, etc.)

```typescript
useEffect(() => {
  const handleSync = () => {
    console.log('Syncing data for this page...')
    fetchData() // Re-fetch data from API
  }

  window.addEventListener('socket-sync', handleSync)
  return () => window.removeEventListener('socket-sync', handleSync)
}, [])
```

### 6.3 Connection Status UI

**Add to Layout.tsx header**:

```typescript
import { useEffect, useState } from 'react'
import { Badge } from 'antd'
import { getSocket } from '../utils/socket'

const ConnectionStatus = () => {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const socket = getSocket()
    if (!socket) return

    socket.on('connect', () => setConnected(true))
    socket.on('disconnect', () => setConnected(false))

    setConnected(socket.connected)

    return () => {
      socket.off('connect')
      socket.off('disconnect')
    }
  }, [])

  return (
    <Badge status={connected ? 'success' : 'error'} text={connected ? 'Connected' : 'Disconnected'} />
  )
}
```

---

## 7. Desktop App UX Requirements

### 7.1 Keyboard Shortcuts

**Implement in**: `frontend/src/App.tsx` or dedicated hook `useKeyboardShortcuts.ts`

| Shortcut | Action | Priority |
|----------|--------|----------|
| `Ctrl+N` (Mac: `Cmd+N`) | New item (context-aware) | HIGH |
| `Ctrl+S` (Mac: `Cmd+S`) | Save current form | HIGH |
| `Ctrl+F` (Mac: `Cmd+F`) | Focus search bar | HIGH |
| `Ctrl+R` (Mac: `Cmd+R`) | Refresh current page data | MEDIUM |
| `Ctrl+P` (Mac: `Cmd+P`) | Print current page | MEDIUM |
| `Ctrl+,` (Mac: `Cmd+,`) | Open settings | LOW |
| `Escape` | Close modal/cancel action | HIGH |
| `F1` | Open help/documentation | LOW |

**Implementation**:

```typescript
// frontend/src/hooks/useKeyboardShortcuts.ts
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export const useKeyboardShortcuts = () => {
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
      const ctrlKey = isMac ? e.metaKey : e.ctrlKey

      if (ctrlKey && e.key === 'n') {
        e.preventDefault()
        console.log('New item shortcut triggered')
        // Dispatch custom event or use context to trigger "new" action
        window.dispatchEvent(new CustomEvent('keyboard-new'))
      }

      if (ctrlKey && e.key === 'f') {
        e.preventDefault()
        const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement
        searchInput?.focus()
      }

      if (ctrlKey && e.key === 'r') {
        e.preventDefault()
        console.log('Refresh shortcut triggered')
        window.dispatchEvent(new CustomEvent('keyboard-refresh'))
      }

      if (e.key === 'Escape') {
        console.log('Escape pressed, closing modals')
        window.dispatchEvent(new CustomEvent('keyboard-escape'))
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [navigate])
}
```

### 7.2 Native Menus (Electron)

**Update**: `main.js` (around line 1000-1050 where menus might be defined)

```javascript
const { Menu } = require('electron')

function createAppMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Maintenance Record',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('menu-new-maintenance')
          }
        },
        { type: 'separator' },
        {
          label: 'Print',
          accelerator: 'CmdOrCtrl+P',
          click: () => {
            mainWindow.webContents.send('menu-print')
          }
        },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Dashboard',
          accelerator: 'CmdOrCtrl+1',
          click: () => {
            mainWindow.webContents.send('menu-navigate', '/')
          }
        },
        {
          label: 'Sites',
          accelerator: 'CmdOrCtrl+2',
          click: () => {
            mainWindow.webContents.send('menu-navigate', '/sites')
          }
        },
        {
          label: 'Machines',
          accelerator: 'CmdOrCtrl+3',
          click: () => {
            mainWindow.webContents.send('menu-navigate', '/machines')
          }
        },
        { type: 'separator' },
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
      ]
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        { type: 'separator' },
        { role: 'front' },
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: () => {
            // Open external documentation URL
            require('electron').shell.openExternal('https://docs.accuratemachinerepair.com')
          }
        },
        {
          label: 'About',
          click: () => {
            mainWindow.webContents.send('menu-about')
          }
        }
      ]
    }
  ]

  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
}

// Call after mainWindow is created
createAppMenu()
```

**Handle in React**: `frontend/src/App.tsx`

```typescript
useEffect(() => {
  // Listen for Electron menu events (if running in Electron)
  if (window.electron) {
    window.electron.ipcRenderer.on('menu-navigate', (path: string) => {
      navigate(path)
    })

    window.electron.ipcRenderer.on('menu-new-maintenance', () => {
      navigate('/maintenance')
    })

    window.electron.ipcRenderer.on('menu-print', () => {
      window.print()
    })

    return () => {
      window.electron.ipcRenderer.removeAllListeners('menu-navigate')
      window.electron.ipcRenderer.removeAllListeners('menu-new-maintenance')
      window.electron.ipcRenderer.removeAllListeners('menu-print')
    }
  }
}, [navigate])
```

### 7.3 Native Notifications

**Add to**: `frontend/src/utils/notifications.ts`

```typescript
export const showNativeNotification = (title: string, body: string) => {
  if (window.Notification && Notification.permission === 'granted') {
    new Notification(title, { body })
  } else if (window.Notification && Notification.permission !== 'denied') {
    Notification.requestPermission().then(permission => {
      if (permission === 'granted') {
        new Notification(title, { body })
      }
    })
  }
}

// Usage: Show notification when overdue items detected
useEffect(() => {
  if (stats && stats.overdue > 0) {
    showNativeNotification(
      'Maintenance Overdue',
      `${stats.overdue} item(s) need immediate attention`
    )
  }
}, [stats])
```

### 7.4 Window State Persistence

**Add to**: `main.js` (Electron)

```javascript
const Store = require('electron-store')
const store = new Store()

function createWindow() {
  // Restore window bounds from store
  const windowBounds = store.get('windowBounds', {
    width: 1280,
    height: 720,
    x: undefined,
    y: undefined
  })

  mainWindow = new BrowserWindow({
    width: windowBounds.width,
    height: windowBounds.height,
    x: windowBounds.x,
    y: windowBounds.y,
    // ... other options
  })

  // Save window bounds on close
  mainWindow.on('close', () => {
    const bounds = mainWindow.getBounds()
    store.set('windowBounds', bounds)
  })
}
```

---

## 8. UI/UX Features to Implement

### 8.1 Loading States

**Current**: Basic `<Spin>` component when loading data
**Improve**: 
- Skeleton screens for initial load (Ant Design `<Skeleton>`)
- Button loading states when submitting forms
- Progress indicators for bulk operations

### 8.2 Error Handling

**Current**: `message.error()` for API failures
**Improve**:
- Toast notifications for transient errors
- Error boundaries for component crashes
- Retry mechanism for failed requests
- Detailed error messages (not just "Failed to load")

### 8.3 Empty States

**Current**: Some pages have empty states
**Improve**:
- Consistent empty state design across all pages
- Actionable CTAs ("Add Your First Site", "Create Machine")
- Illustrations or icons for visual appeal

### 8.4 Mobile Responsiveness

**Current**: Ant Design components are responsive by default
**Improve**:
- Test all pages on mobile viewport (375px width)
- Hide columns on mobile with responsive `<Table>` config
- Use drawer instead of modal on mobile for forms
- Touch-friendly buttons (min 44px height)

### 8.5 Accessibility

**Current**: Basic HTML semantics
**Improve**:
- ARIA labels for all interactive elements
- Keyboard navigation for all actions (Tab, Enter, Escape)
- Focus management for modals
- Screen reader announcements for dynamic content
- High contrast mode support

### 8.6 Print Support

**Current**: Basic print CSS in legacy app
**Improve**:
- Print-specific React component that renders only for print
- Hide navigation/sidebar/buttons when printing
- Expand all collapsed content
- Page break handling for long tables

---

## 9. API Contract Reference

### 9.1 Authentication

**POST /api/v1/auth/login**
```json
// Request
{
  "username": "admin",
  "password": "password123"
}

// Response
{
  "data": {
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "permissions": ["sites.view", "sites.create", "machines.view", ...]
    }
  },
  "message": "Login successful",
  "status": "success",
  "meta": {
    "login_feedback": {
      "attempt_id": "2f31c2a4",
      "final_status": "session_ready",
      "steps": [
        { "key": "credentials", "label": "Verify credentials", "status": "success" },
        { "key": "session", "label": "Secure session", "status": "success" },
        { "key": "trust_device", "label": "Trust this device", "status": "success" },
        { "key": "workspace", "label": "Prepare workspace", "status": "pending" }
      ]
    }
  }
}
```

**GET /api/v1/auth/me**
```json
// Response
{
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "permissions": ["sites.view", "sites.create", ...]
  },
  "status": "success"
}
```

### 9.2 Dashboard

**GET /api/v1/dashboard**
```json
// Response
{
  "data": {
    "total_machines": 25,
    "overdue": 8,
    "due_soon": 12,
    "completed": 34
  },
  "message": "Dashboard data retrieved successfully",
  "status": "success"
}
```

### 9.3 Sites

**GET /api/v1/sites**
```json
// Response
{
  "data": [
    {
      "id": 1,
      "name": "Main Plant",
      "location": "123 Industrial Ave",
      "contact_email": "plant@example.com",
      "machine_count": 12,
      "overdue_parts": 3,
      "due_soon_parts": 5
    },
    ...
  ],
  "status": "success"
}
```

**POST /api/v1/sites**
```json
// Request
{
  "name": "New Plant",
  "location": "456 Factory Rd",
  "contact_email": "newplant@example.com"
}

// Response
{
  "data": {
    "id": 2,
    "name": "New Plant",
    "location": "456 Factory Rd",
    "contact_email": "newplant@example.com"
  },
  "message": "Site created successfully",
  "status": "success"
}
```

**PUT /api/v1/sites/:id**
**DELETE /api/v1/sites/:id**

### 9.4 Machines

**GET /api/v1/machines**
**GET /api/v1/machines?site_id=1**
```json
// Response
{
  "data": [
    {
      "id": 1,
      "name": "CNC Mill #1",
      "model": "Haas VF-2",
      "serial_number": "12345",
      "site_id": 1,
      "site_name": "Main Plant",
      "parts_count": 8,
      "decommissioned": false
    },
    ...
  ],
  "status": "success"
}
```

**POST /api/v1/machines**
**PUT /api/v1/machines/:id**
**DELETE /api/v1/machines/:id**

### 9.5 Maintenance

**GET /api/v1/maintenance?status=overdue**
```json
// Response
{
  "data": [
    {
      "id": 1,
      "part_id": 5,
      "part_name": "Hydraulic Oil",
      "machine_id": 1,
      "machine_name": "CNC Mill #1",
      "site_id": 1,
      "site_name": "Main Plant",
      "next_maintenance": "2025-10-15",
      "days_overdue": 18,
      "maintenance_frequency": 30,
      "maintenance_unit": "days"
    },
    ...
  ],
  "status": "success"
}
```

**GET /api/v1/maintenance?status=due_soon**
```json
// Response (similar structure, but days_until instead of days_overdue)
{
  "data": [
    {
      "id": 2,
      "part_id": 8,
      "part_name": "Air Filter",
      "machine_id": 2,
      "machine_name": "Lathe #3",
      "site_id": 1,
      "site_name": "Main Plant",
      "next_maintenance": "2025-11-08",
      "days_until": 5,
      "maintenance_frequency": 14,
      "maintenance_unit": "days"
    },
    ...
  ],
  "status": "success"
}
```

**POST /api/v1/maintenance**
```json
// Request
{
  "site_id": 1,
  "machine_id": 1,
  "part_id": 5,
  "maintenance_type": "Scheduled",
  "date": "2025-11-02",
  "description": "Changed hydraulic oil",
  "notes": "Oil was dirty, changed filter as well"
}

// Response
{
  "data": {
    "id": 123,
    "machine_id": 1,
    "part_id": 5,
    "maintenance_type": "Scheduled",
    "date": "2025-11-02",
    "description": "Changed hydraulic oil",
    "notes": "Oil was dirty, changed filter as well",
    "performed_by": "admin",
    "created_at": "2025-11-02T14:30:00Z"
  },
  "message": "Maintenance record created successfully",
  "status": "success"
}
```

### 9.6 Audits

**GET /api/v1/audits**
**POST /api/v1/audits**
**PUT /api/v1/audits/:id**
**DELETE /api/v1/audits/:id**

**POST /api/v1/audits/:id/complete**
```json
// Request
{
  "completed_at": "2025-11-02T15:00:00Z",
  "notes": "All checks passed"
}

// Response
{
  "data": {
    "id": 456,
    "audit_task_id": 10,
    "completed_by": "admin",
    "completed_at": "2025-11-02T15:00:00Z",
    "notes": "All checks passed"
  },
  "message": "Audit task completed successfully",
  "status": "success"
}
```

### 9.7 Users (Admin only)

**GET /api/v1/users**
**POST /api/v1/users**
**PUT /api/v1/users/:id**
**DELETE /api/v1/users/:id**

---

## 10. Implementation Checklist

### Phase 1: Dashboard Fix (IMMEDIATE)

- [ ] **Update Dashboard.tsx to fetch real API data** (HIGH)
  - [ ] Update `DashboardStats` interface with correct fields
  - [ ] Add `OverdueItem` and `DueSoonItem` interfaces
  - [ ] Fetch `/api/v1/dashboard` for stats
  - [ ] Fetch `/api/v1/maintenance?status=overdue` for overdue items
  - [ ] Fetch `/api/v1/maintenance?status=due_soon` for due soon items
  - [ ] Remove hardcoded `recentTasksData` array
  - [ ] Add two separate tables: "Overdue Maintenance" and "Due Soon"
  - [ ] Test with real database data

- [ ] **Add Site Filter to Dashboard** (MEDIUM)
  - [ ] Fetch all sites from `/api/v1/sites`
  - [ ] Add `<Select>` dropdown to filter by site
  - [ ] Filter overdue/due-soon items by selected site
  - [ ] Update stats cards to reflect filtered data
  - [ ] Add "All Sites" option to reset filter

- [ ] **Add Quick Action Buttons** (LOW)
  - [ ] "Record Maintenance Now" → Navigate to `/maintenance`
  - [ ] "View X Overdue Items" → Scroll to overdue table

### Phase 2: SocketIO Real-Time Sync (HIGH)

- [ ] **Install and Configure SocketIO Client**
  - [ ] Run `npm install socket.io-client` in frontend
  - [ ] Create `frontend/src/utils/socket.ts` with connection logic
  - [ ] Initialize socket in `App.tsx` on mount
  - [ ] Disconnect socket on unmount

- [ ] **Implement Sync Event Handling**
  - [ ] Listen to `sync` event from server
  - [ ] Dispatch custom `socket-sync` event to all components
  - [ ] Update Dashboard to refresh data on sync event
  - [ ] Update Sites/Machines/Audits to refresh data on sync event

- [ ] **Add Connection Status UI**
  - [ ] Create `<ConnectionStatus>` component
  - [ ] Show badge in header (green: connected, red: disconnected)
  - [ ] Update badge on `connect`/`disconnect` events

- [ ] **Handle Reconnection**
  - [ ] Implement exponential backoff for reconnection
  - [ ] Prevent reconnection during sync operations
  - [ ] Show toast notification on reconnection success/failure

### Phase 3: Desktop UX Polish (HIGH)

- [ ] **Keyboard Shortcuts**
  - [ ] Create `useKeyboardShortcuts` hook
  - [ ] Implement `Ctrl+N` (New item, context-aware)
  - [ ] Implement `Ctrl+F` (Focus search bar)
  - [ ] Implement `Ctrl+R` (Refresh current page data)
  - [ ] Implement `Escape` (Close modal/cancel action)
  - [ ] Implement `Ctrl+P` (Print current page)
  - [ ] Test all shortcuts on Windows, Mac, and Linux

- [ ] **Native Menus (Electron)**
  - [ ] Update `main.js` with `Menu.buildFromTemplate()`
  - [ ] Add File menu (New, Print, Quit)
  - [ ] Add Edit menu (Undo, Redo, Copy, Paste)
  - [ ] Add View menu (Dashboard, Sites, Machines, Reload, DevTools)
  - [ ] Add Help menu (Documentation, About)
  - [ ] Send IPC messages to React on menu click
  - [ ] Handle IPC messages in `App.tsx` to trigger actions

- [ ] **Native Notifications**
  - [ ] Create `showNativeNotification()` utility
  - [ ] Request notification permission on first launch
  - [ ] Show notification when overdue items detected
  - [ ] Show notification on sync event (optional, configurable)

- [ ] **Window State Persistence**
  - [ ] Install `electron-store` in Electron app
  - [ ] Save window bounds (width, height, x, y) on close
  - [ ] Restore window bounds on app launch
  - [ ] Save maximized state
  - [ ] Restore maximized state

### Phase 4: Advanced Dashboard Features (MEDIUM)

- [ ] **Site Accordion with Machine List**
  - [ ] Fetch machines grouped by site
  - [ ] Use Ant Design `<Collapse>` for site accordion
  - [ ] Show site stats (overdue/due-soon) in panel header
  - [ ] Render machine list inside each panel
  - [ ] Add "Toggle Parts" button per machine

- [ ] **Collapsible Parts Table per Machine**
  - [ ] Fetch parts for each machine
  - [ ] Use nested `<Collapse>` for parts
  - [ ] Show part status badges (overdue/due-soon/ok)
  - [ ] Calculate machine status from part statuses
  - [ ] Update machine status badge dynamically

- [ ] **Decommissioned Toggle**
  - [ ] Add `<Switch>` to show/hide decommissioned machines
  - [ ] Filter machines by `decommissioned` field
  - [ ] Persist toggle state to localStorage

### Phase 5: UI/UX Enhancements (MEDIUM)

- [ ] **Loading States**
  - [ ] Replace `<Spin>` with `<Skeleton>` for initial load
  - [ ] Add loading prop to buttons when submitting
  - [ ] Show progress for bulk operations (multi-part maintenance)

- [ ] **Error Handling**
  - [ ] Add error boundaries for component crashes
  - [ ] Show detailed error messages (not just "Failed to load")
  - [ ] Implement retry mechanism for failed API calls
  - [ ] Log errors to console for debugging

- [ ] **Empty States**
  - [ ] Create reusable `<EmptyState>` component
  - [ ] Add to all pages (Sites, Machines, Audits, etc.)
  - [ ] Include icon, title, description, and CTA button
  - [ ] Use consistent design (Ant Design `<Empty>` component)

- [ ] **Mobile Responsiveness**
  - [ ] Test all pages on mobile viewport (375px width)
  - [ ] Hide columns on mobile with `responsive` prop
  - [ ] Use `<Drawer>` instead of `<Modal>` on mobile for forms
  - [ ] Ensure buttons are touch-friendly (min 44px height)
  - [ ] Test on physical devices (iOS, Android)

- [ ] **Accessibility**
  - [ ] Add ARIA labels to all interactive elements
  - [ ] Test keyboard navigation (Tab, Enter, Escape)
  - [ ] Add focus styles for keyboard users
  - [ ] Test with screen reader (NVDA, VoiceOver)
  - [ ] Run Lighthouse accessibility audit

### Phase 6: Print Support (LOW)

- [ ] **Print-Specific Styling**
  - [ ] Create `print.css` for React components
  - [ ] Hide navigation, sidebar, buttons when printing
  - [ ] Expand all collapsed content
  - [ ] Handle page breaks for long tables
  - [ ] Test print preview in Chrome, Firefox, Safari

- [ ] **Print Action**
  - [ ] Add "Print" button to pages (Dashboard, Sites, Machines)
  - [ ] Trigger `window.print()` on click
  - [ ] Handle print in Electron menu (Ctrl+P)

### Phase 7: Testing & Documentation (LOW)

- [ ] **Unit Tests**
  - [ ] Write tests for API client (`api.ts`)
  - [ ] Write tests for SocketIO client (`socket.ts`)
  - [ ] Write tests for keyboard shortcuts hook
  - [ ] Run tests with `npm test`

- [ ] **Integration Tests**
  - [ ] Test login flow (login → dashboard → logout)
  - [ ] Test CRUD operations (create site → edit → delete)
  - [ ] Test real-time sync (open two windows, create item in one, verify update in other)

- [ ] **Documentation**
  - [ ] Update `README.md` with React frontend instructions
  - [ ] Document keyboard shortcuts in app (Help menu or modal)
  - [ ] Document SocketIO events and how to test
  - [ ] Add JSDoc comments to utility functions
  - [ ] Create user guide for desktop app features

### Phase 8: Performance & Optimization (LOW)

- [ ] **Code Splitting**
  - [ ] Use React lazy loading for page components
  - [ ] Split vendor bundles (React, Ant Design, etc.)
  - [ ] Reduce bundle size (currently 599KB)

- [ ] **Caching**
  - [ ] Implement API response caching (React Query or SWR)
  - [ ] Cache site/machine lists in memory
  - [ ] Invalidate cache on sync event

- [ ] **Image Optimization**
  - [ ] Optimize logo and icons for smaller size
  - [ ] Use WebP format for images
  - [ ] Lazy load images below the fold

---

## Appendix A: File Manifest

### Legacy Frontend Files (to reference, not edit)

**Core Templates** (138 total):
- `templates/dashboard.html` (781 lines) - Main dashboard
- `templates/sites.html` (264 lines) - Sites CRUD
- `templates/machines.html` (298 lines) - Machines CRUD
- `templates/audits.html` (445 lines) - Audits CRUD
- `templates/maintenance.html` (391 lines) - Maintenance recording
- `templates/parts.html` - Parts CRUD
- `templates/admin_users.html` - User management
- `templates/login.html` - Authentication
- `templates/base.html` (1010 lines) - Base layout
- `templates/includes/`, `templates/partials/` - Shared components

**Core JavaScript** (28 total):
- `static/js/dashboard.js` (516 lines) - Dashboard logic
- `static/js/socket-sync.js` (273 lines) - Real-time sync
- `static/js/app.js` (210 lines) - Common functionality
- `static/js/ux-enhancements.js` - UX improvements
- `static/js/ajax-loader.js` - AJAX utilities
- Multiple hamburger/sidebar toggle scripts

**Core CSS** (68 total):
- `static/css/amrs-theme.css` - Main theme
- `static/css/main.css` - Core styles
- `static/css/modern-ui.css` - Modern UI components
- `static/css/responsive-enhancements.css` - Mobile responsive
- `static/css/print.css` - Print styles
- `static/css/dark-mode-comprehensive-fix.css` - Dark mode
- `static/css/ux-enhancements.css` - UX styling

### React Frontend Files (to edit)

**Pages**:
- `frontend/src/pages/Dashboard.tsx` - ❌ NEEDS FIXING
- `frontend/src/pages/Sites.tsx` - ✅ Working
- `frontend/src/pages/Machines.tsx` - ✅ Working
- `frontend/src/pages/Audits.tsx` - ✅ Working
- `frontend/src/pages/Maintenance.tsx` - ⚠️ Needs review
- `frontend/src/pages/Users.tsx` - ✅ Working
- `frontend/src/pages/Login.tsx` - ✅ Working

**Components**:
- `frontend/src/components/Layout.tsx` - Main layout
- `frontend/src/components/sites/` - Site modals
- `frontend/src/components/machines/` - Machine modals
- `frontend/src/components/audits/` - Audit modals
- `frontend/src/components/users/` - User modals

**Utils**:
- `frontend/src/utils/api.ts` - ✅ Working (Axios client)
- `frontend/src/utils/socket.ts` - ❌ TO CREATE (SocketIO client)
- `frontend/src/utils/notifications.ts` - ❌ TO CREATE (Native notifications)

**Hooks**:
- `frontend/src/hooks/useKeyboardShortcuts.ts` - ❌ TO CREATE

**Backend**:
- `api_v1.py` - ✅ Fixed (API endpoints)
- `app.py` - ✅ Fixed (Flask app, serves React)
- `models.py` - ✅ Correct schema

**Electron**:
- `main.js` - ⚠️ Needs menu updates

---

## Appendix B: Color Palette & Design Tokens

### Colors (from `static/css/amrs-theme.css`)

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| Primary | `#005cbf` | `#4da6ff` | Buttons, links |
| Success | `#28a745` | `#4caf50` | Success states |
| Danger | `#d9534f` | `#f44336` | Error states, overdue |
| Warning | `#f0ad4e` | `#ff9800` | Warning states, due soon |
| Info | `#5bc0de` | `#03a9f4` | Info states |
| Background | `#ffffff` | `#181a1b` | Page background |
| Surface | `#f8f9fa` | `#242526` | Cards, modals |
| Text | `#212529` | `#e8e6e3` | Primary text |
| Text Secondary | `#6c757d` | `#aaa` | Secondary text |

### Typography

| Element | Font Size | Weight | Line Height |
|---------|-----------|--------|-------------|
| H1 | 2rem | 600 | 1.2 |
| H2 | 1.5rem | 600 | 1.3 |
| H3 | 1.25rem | 600 | 1.4 |
| Body | 1rem | 400 | 1.5 |
| Small | 0.875rem | 400 | 1.4 |

### Spacing (Ant Design default)

| Token | Value |
|-------|-------|
| xs | 8px |
| sm | 12px |
| md | 16px |
| lg | 24px |
| xl | 32px |

---

## Appendix C: Priority Matrix

| Task | Priority | Complexity | Impact | Dependencies |
|------|----------|------------|--------|--------------|
| Dashboard API Fix | 🔴 HIGH | Low | High | None |
| Dashboard Tables (Overdue/Due Soon) | 🔴 HIGH | Medium | High | Dashboard API Fix |
| SocketIO Integration | 🔴 HIGH | High | High | None |
| Keyboard Shortcuts | 🔴 HIGH | Medium | Medium | None |
| Native Menus | 🔴 HIGH | Medium | Medium | Keyboard Shortcuts |
| Site Filter (Dashboard) | 🟡 MEDIUM | Low | Medium | Dashboard API Fix |
| Decommissioned Toggle | 🟡 MEDIUM | Low | Low | Dashboard API Fix |
| Site Accordion | 🟡 MEDIUM | High | Medium | Dashboard Tables |
| Native Notifications | 🟡 MEDIUM | Low | Low | None |
| Connection Status UI | 🟡 MEDIUM | Low | Low | SocketIO Integration |
| Loading States | 🟡 MEDIUM | Low | Medium | None |
| Error Handling | 🟡 MEDIUM | Medium | Medium | None |
| Empty States | 🟡 MEDIUM | Low | Low | None |
| Mobile Responsiveness | 🟡 MEDIUM | Medium | Medium | None |
| Accessibility | 🟡 MEDIUM | High | High | None |
| Print Support | 🟢 LOW | Low | Low | None |
| Window State Persistence | 🟢 LOW | Low | Low | None |
| Unit Tests | 🟢 LOW | High | Medium | All features |
| Documentation | 🟢 LOW | Low | Low | All features |
| Code Splitting | 🟢 LOW | Medium | Low | None |
| Caching | 🟢 LOW | High | Medium | SocketIO Integration |

---

## Appendix D: Testing Checklist

### Manual Testing

**Dashboard**:
- [ ] Stats cards show correct counts from database
- [ ] Site filter updates stats and tables
- [ ] Overdue table shows correct items with days overdue
- [ ] Due soon table shows correct items with days until
- [ ] Quick action buttons navigate correctly
- [ ] Refresh button fetches new data

**SocketIO**:
- [ ] Connection badge shows "Connected" when socket is active
- [ ] Open two windows, create item in one, verify it appears in the other
- [ ] Disconnect network, verify "Disconnected" badge and reconnection attempt
- [ ] Check console for SocketIO logs (connect, sync, disconnect)

**Keyboard Shortcuts**:
- [ ] `Ctrl+N` triggers new item action (context-aware)
- [ ] `Ctrl+F` focuses search bar
- [ ] `Ctrl+R` refreshes current page data
- [ ] `Escape` closes modal
- [ ] `Ctrl+P` opens print dialog

**Native Menus**:
- [ ] File → New Maintenance Record navigates to `/maintenance`
- [ ] View → Dashboard navigates to `/`
- [ ] View → Sites navigates to `/sites`
- [ ] Edit → Copy/Paste works in text fields

**Mobile**:
- [ ] All pages render correctly on 375px width
- [ ] Tables show horizontal scroll hint on mobile
- [ ] Buttons are touch-friendly (min 44px height)
- [ ] Modals/drawers open correctly on mobile

### Automated Testing

**API Client**:
```bash
npm run test -- api.test.ts
```

**SocketIO Client**:
```bash
npm run test -- socket.test.ts
```

**Keyboard Shortcuts**:
```bash
npm run test -- useKeyboardShortcuts.test.ts
```

---

## Appendix E: Common Pitfalls & Solutions

### 1. CORS Issues
**Problem**: API calls fail with CORS error even though same-origin.
**Solution**: Ensure React is served from Flask (`http://127.0.0.1:10000/`), not `file://`. Verify `withCredentials: true` in Axios client.

### 2. Session Cookie Not Sent
**Problem**: Authentication succeeds but subsequent API calls return 401.
**Solution**: Add `withCredentials: true` to Axios client. Verify `SESSION_COOKIE_SAMESITE = 'Lax'` in Flask config.

### 3. SocketIO Connection Fails
**Problem**: Socket connects but immediately disconnects.
**Solution**: Check Flask-SocketIO version matches client version. Verify CORS settings in Flask-SocketIO. Start with `polling` transport, upgrade to `websocket`.

### 4. Dashboard Stats Show 0
**Problem**: Stats cards show 0 even though data exists in database.
**Solution**: Verify API endpoint returns correct schema. Check database schema (parts have `next_maintenance`, not MaintenanceRecords). Use SQLite browser to inspect data.

### 5. Keyboard Shortcuts Not Working
**Problem**: `Ctrl+N` does nothing.
**Solution**: Ensure `preventDefault()` is called to prevent default browser behavior. Check if event bubbling is stopped. Verify Mac uses `metaKey` instead of `ctrlKey`.

### 6. Native Menus Not Showing
**Problem**: Electron app shows no menu bar.
**Solution**: Ensure `Menu.setApplicationMenu(menu)` is called after creating menu. On Mac, menu always shows (in system bar). On Windows/Linux, menu is in window.

### 7. React Build Fails
**Problem**: `npm run build` fails with TypeScript errors.
**Solution**: Run `npm run type-check` to see detailed errors. Fix type errors in components. Ensure all imports have correct paths.

### 8. Electron App Crashes on Launch
**Problem**: White screen or app crashes immediately.
**Solution**: Check console logs in DevTools (`Ctrl+Shift+I`). Verify Flask backend is running on port 10000. Check `main.js` for errors.

---

## Conclusion

This blueprint provides a comprehensive roadmap for completing the React frontend migration. **Start with Phase 1 (Dashboard Fix)** as it's the highest priority and easiest to implement. Then proceed with Phase 2 (SocketIO) and Phase 3 (Desktop UX) for maximum impact.

All legacy features have been documented with implementation guidance. Use this document as a reference when implementing each feature. Test thoroughly on Windows, Mac, and Linux.

**Estimated Timeline**:
- Phase 1 (Dashboard Fix): 2-4 hours
- Phase 2 (SocketIO): 4-6 hours
- Phase 3 (Desktop UX): 6-8 hours
- Phase 4 (Advanced Dashboard): 8-10 hours
- Phase 5 (UI/UX): 4-6 hours
- Phase 6 (Print): 2-3 hours
- Phase 7 (Testing): 4-6 hours
- Phase 8 (Optimization): 4-6 hours

**Total**: 34-49 hours (1-1.5 weeks of focused development)

**Next Steps**:
1. Read this entire document carefully
2. Prioritize tasks based on your immediate needs
3. Start with Dashboard fix (quick win)
4. Implement features incrementally, testing each before moving to next
5. Update this document as you discover new requirements
