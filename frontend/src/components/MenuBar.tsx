import React, { useState } from 'react'
import { Menu, Dropdown, Space } from 'antd'
import type { MenuProps } from 'antd'
import { DownOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import ConnectionStatus from './ConnectionStatus'
import { useAuthorization } from '../hooks/useAuthorization'
import '../styles/menubar.css'

const MenuBar: React.FC = () => {
  const { logout } = useAuth()
  const { isAdmin, hasPermission } = useAuthorization()
  const [activeMenu, setActiveMenu] = useState<string | null>(null)

  const canViewReports = hasPermission('reports.view') || isAdmin
  const canImportData = isAdmin

  const fileMenuItems: MenuProps['items'] = []
  fileMenuItems.push({
    key: 'new',
    label: 'New',
    children: [
      { key: 'new-machine', label: 'Machine' },
      { key: 'new-task', label: 'Maintenance Task' },
      { key: 'new-audit', label: 'Audit' },
    ],
  })
  fileMenuItems.push({ type: 'divider' })
  if (canViewReports) {
    fileMenuItems.push({ key: 'export', label: 'Export' })
  }
  if (canImportData) {
    fileMenuItems.push({ key: 'import', label: 'Import' })
  }
  fileMenuItems.push({ type: 'divider' })
  fileMenuItems.push({ key: 'exit', label: 'Exit', onClick: () => logout() })

  const editMenuItems: MenuProps['items'] = [
    { key: 'undo', label: 'Undo', disabled: true },
    { key: 'redo', label: 'Redo', disabled: true },
    { type: 'divider' },
    { key: 'preferences', label: 'Preferences' },
  ]

  const viewMenuItems: MenuProps['items'] = []
  viewMenuItems.push({ key: 'dashboard', label: 'Dashboard' })
  if (hasPermission('machines.view') || isAdmin) {
    viewMenuItems.push({ key: 'machines', label: 'Machines' })
  }
  if (hasPermission('maintenance.view') || isAdmin) {
    viewMenuItems.push({ key: 'maintenance', label: 'Maintenance' })
  }
  if (hasPermission('audits.view') || hasPermission('audits.access') || isAdmin) {
    viewMenuItems.push({ key: 'audits', label: 'Audits' })
  }
  if (hasPermission('sites.view') || isAdmin) {
    viewMenuItems.push({ key: 'sites', label: 'Sites' })
  }
  if (canViewReports) {
    viewMenuItems.push({ key: 'reports', label: 'Reports' })
  }
  viewMenuItems.push({ type: 'divider' })
  viewMenuItems.push({ key: 'refresh', label: 'Refresh' })

  const toolsMenuItems: MenuProps['items'] = []
  toolsMenuItems.push({ key: 'sync', label: 'Sync Now' })
  if (canViewReports) {
    toolsMenuItems.push({ key: 'reports', label: 'Reports' })
  }
  toolsMenuItems.push({ type: 'divider' })
  if (isAdmin || hasPermission('admin.view')) {
    toolsMenuItems.push({ key: 'settings', label: 'Settings' })
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
        <ConnectionStatus />
      </div>
    </div>
  )
}

export default MenuBar
