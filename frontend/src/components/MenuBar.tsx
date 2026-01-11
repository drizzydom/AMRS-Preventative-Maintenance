import React, { useState } from 'react'
import { Menu, Dropdown, Space, Button, Tooltip } from 'antd'
import type { MenuProps } from 'antd'
import { DownOutlined, BulbOutlined, BulbFilled } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import ConnectionStatus from './ConnectionStatus'
import { useAuthorization } from '../hooks/useAuthorization'
import EmergencyMaintenanceModal from './modals/EmergencyMaintenanceModal'
import '../styles/menubar.css'

const MenuBar: React.FC = () => {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const { isAdmin, hasPermission } = useAuthorization()
  const { isDark, toggleTheme } = useTheme()
  const [activeMenu, setActiveMenu] = useState<string | null>(null)
  const [emergencyModalOpen, setEmergencyModalOpen] = useState(false)

  const canViewReports = hasPermission('reports.view') || isAdmin
  const canImportData = isAdmin

  const fileMenuItems: MenuProps['items'] = []
  fileMenuItems.push({
    key: 'new',
    label: 'New',
    children: [
      { key: 'new-machine', label: 'Machine', onClick: () => navigate('/machines') },
      { key: 'new-task', label: 'Maintenance Task', onClick: () => navigate('/maintenance') },
      { key: 'new-emergency', label: 'Emergency Maintenance', onClick: () => setEmergencyModalOpen(true) },
      { key: 'new-audit', label: 'Audit', onClick: () => navigate('/audits') },
    ],
  })
  fileMenuItems.push({ type: 'divider' })
  if (canViewReports) {
    fileMenuItems.push({ key: 'export', label: 'Export', onClick: () => navigate('/reports') })
  }
  if (canImportData) {
    fileMenuItems.push({ key: 'import', label: 'Import', onClick: () => navigate('/admin') })
  }
  fileMenuItems.push({ type: 'divider' })
  fileMenuItems.push({ key: 'exit', label: 'Exit', onClick: () => logout() })

  const editMenuItems: MenuProps['items'] = [
    { key: 'undo', label: 'Undo', disabled: true },
    { key: 'redo', label: 'Redo', disabled: true },
    { type: 'divider' },
    { key: 'preferences', label: 'Preferences', onClick: () => navigate('/settings') },
  ]

  const viewMenuItems: MenuProps['items'] = []
  viewMenuItems.push({ key: 'dashboard', label: 'Dashboard', onClick: () => navigate('/dashboard') })
  if (hasPermission('machines.view') || isAdmin) {
    viewMenuItems.push({ key: 'machines', label: 'Machines', onClick: () => navigate('/machines') })
  }
  if (hasPermission('maintenance.view') || isAdmin) {
    viewMenuItems.push({ key: 'maintenance', label: 'Maintenance', onClick: () => navigate('/maintenance') })
    viewMenuItems.push({ key: 'maintenance-records', label: 'Maintenance Records', onClick: () => navigate('/maintenance-records') })
  }
  if (hasPermission('audits.view') || hasPermission('audits.access') || isAdmin) {
    viewMenuItems.push({ key: 'audits', label: 'Audits', onClick: () => navigate('/audits') })
  }
  if (hasPermission('sites.view') || isAdmin) {
    viewMenuItems.push({ key: 'sites', label: 'Sites', onClick: () => navigate('/sites') })
  }
  if (canViewReports) {
    viewMenuItems.push({ key: 'reports', label: 'Reports', onClick: () => navigate('/reports') })
  }
  viewMenuItems.push({ type: 'divider' })
  viewMenuItems.push({ 
    key: 'refresh', 
    label: 'Refresh', 
    onClick: () => window.dispatchEvent(new Event('keyboard-refresh')) 
  })

  const toolsMenuItems: MenuProps['items'] = []
  toolsMenuItems.push({ 
    key: 'sync', 
    label: 'Sync Now',
    onClick: () => window.dispatchEvent(new Event('socket-sync')) 
  })
  if (canViewReports) {
    toolsMenuItems.push({ key: 'reports', label: 'Reports', onClick: () => navigate('/reports') })
  }
  toolsMenuItems.push({ type: 'divider' })
  if (isAdmin || hasPermission('admin.view')) {
    toolsMenuItems.push({ key: 'settings', label: 'Settings', onClick: () => navigate('/settings') })
  }

  const helpMenuItems: MenuProps['items'] = [
    { key: 'documentation', label: 'Documentation' },
    { key: 'shortcuts', label: 'Keyboard Shortcuts' },
    { type: 'divider' },
    { key: 'about', label: 'About' },
  ]

  return (
    <div className="menu-bar">
      <div className="menu-bar-left">
        <Dropdown menu={{ items: fileMenuItems }} trigger={['click']}>
          <a onClick={(e) => e.preventDefault()}>
            <Space>
              File
              <DownOutlined style={{ fontSize: '10px' }} />
            </Space>
          </a>
        </Dropdown>
        <Dropdown menu={{ items: editMenuItems }} trigger={['click']}>
          <a onClick={(e) => e.preventDefault()}>
            <Space>
              Edit
              <DownOutlined style={{ fontSize: '10px' }} />
            </Space>
          </a>
        </Dropdown>
        <Dropdown menu={{ items: viewMenuItems }} trigger={['click']}>
          <a onClick={(e) => e.preventDefault()}>
            <Space>
              View
              <DownOutlined style={{ fontSize: '10px' }} />
            </Space>
          </a>
        </Dropdown>
        <Dropdown menu={{ items: toolsMenuItems }} trigger={['click']}>
          <a onClick={(e) => e.preventDefault()}>
            <Space>
              Tools
              <DownOutlined style={{ fontSize: '10px' }} />
            </Space>
          </a>
        </Dropdown>
        <Dropdown menu={{ items: helpMenuItems }} trigger={['click']}>
          <a onClick={(e) => e.preventDefault()}>
            <Space>
              Help
              <DownOutlined style={{ fontSize: '10px' }} />
            </Space>
          </a>
        </Dropdown>
      </div>
      <div className="menu-bar-right">
        <Tooltip title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
          <Button
            type="text"
            size="small"
            icon={isDark ? <BulbFilled style={{ color: '#faad14' }} /> : <BulbOutlined />}
            onClick={toggleTheme}
            style={{ marginRight: 12 }}
          />
        </Tooltip>
        <ConnectionStatus />
      </div>

      <EmergencyMaintenanceModal
        open={emergencyModalOpen}
        onClose={() => setEmergencyModalOpen(false)}
        onSuccess={() => window.dispatchEvent(new Event('socket-sync'))}
      />
    </div>
  )
}

export default MenuBar
