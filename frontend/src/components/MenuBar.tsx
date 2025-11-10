import React, { useState } from 'react'
import { Menu, Dropdown, Space } from 'antd'
import type { MenuProps } from 'antd'
import { DownOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import ConnectionStatus from './ConnectionStatus'
import '../styles/menubar.css'

const MenuBar: React.FC = () => {
  const { logout } = useAuth()
  const [activeMenu, setActiveMenu] = useState<string | null>(null)

  const fileMenuItems: MenuProps['items'] = [
    {
      key: 'new',
      label: 'New',
      children: [
        { key: 'new-machine', label: 'Machine' },
        { key: 'new-task', label: 'Maintenance Task' },
        { key: 'new-audit', label: 'Audit' },
      ],
    },
    { type: 'divider' },
    { key: 'export', label: 'Export' },
    { key: 'import', label: 'Import' },
    { type: 'divider' },
    { key: 'exit', label: 'Exit', onClick: () => logout() },
  ]

  const editMenuItems: MenuProps['items'] = [
    { key: 'undo', label: 'Undo', disabled: true },
    { key: 'redo', label: 'Redo', disabled: true },
    { type: 'divider' },
    { key: 'preferences', label: 'Preferences' },
  ]

  const viewMenuItems: MenuProps['items'] = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'machines', label: 'Machines' },
    { key: 'maintenance', label: 'Maintenance' },
    { key: 'audits', label: 'Audits' },
    { key: 'sites', label: 'Sites' },
    { type: 'divider' },
    { key: 'refresh', label: 'Refresh' },
  ]

  const toolsMenuItems: MenuProps['items'] = [
    { key: 'sync', label: 'Sync Now' },
    { key: 'reports', label: 'Reports' },
    { type: 'divider' },
    { key: 'settings', label: 'Settings' },
  ]

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
