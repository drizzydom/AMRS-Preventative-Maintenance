import React, { useMemo, useState } from 'react'
import { Layout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  ToolOutlined,
  CheckSquareOutlined,
  SettingOutlined,
  TeamOutlined,
  EnvironmentOutlined,
  FileTextOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SafetyOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthorization } from '../hooks/useAuthorization'
import { useAuth } from '../contexts/AuthContext'
import '../styles/sidebar.css'

const { Sider } = Layout

type MenuItem = Required<MenuProps>['items'][number]

const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { isAdmin, hasPermission } = useAuthorization()
  const { user, logout } = useAuth()

  const roleLabel = useMemo(() => {
    if (!user) {
      return ''
    }
    if (user.is_admin) {
      return 'Administrator'
    }
    if (user.role) {
      const normalized = user.role.replace(/_/g, ' ')
      return normalized.charAt(0).toUpperCase() + normalized.slice(1)
    }
    return ''
  }, [user])

  const navItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      visible: true,
    },
    {
      key: '/machines',
      icon: <ToolOutlined />,
      label: 'Machines',
      visible: hasPermission('machines.view') || hasPermission('maintenance.record') || isAdmin,
    },
    {
      key: '/maintenance',
      icon: <SettingOutlined />,
      label: 'Maintenance',
      visible: hasPermission('maintenance.view') || hasPermission('maintenance.record') || isAdmin,
    },
    {
      key: '/audits',
      icon: <CheckSquareOutlined />,
      label: 'Audits',
      visible: hasPermission('audits.access') || hasPermission('audits.view') || isAdmin,
    },
    {
      key: '/sites',
      icon: <EnvironmentOutlined />,
      label: 'Sites',
      visible: hasPermission('sites.view') || isAdmin,
    },
    {
      key: '/reports',
      icon: <FileTextOutlined />,
      label: 'Reports',
      visible: hasPermission('reports.view') || isAdmin,
    },
    {
      key: '/users',
      icon: <TeamOutlined />,
      label: 'Users',
      visible: isAdmin,
    },
    {
      key: '/admin',
      icon: <SafetyOutlined />,
      label: 'Admin Panel',
      visible: isAdmin,
    },
  ]

  const items: MenuItem[] = navItems
    .filter((item) => item.visible)
    .map(({ visible, ...item }) => item)

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key)
  }

  const selectedKey = location.pathname

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={(value) => setCollapsed(value)}
      trigger={null}
      className="app-sidebar"
      width={200}
    >
      <div className="sidebar-shell">
        <div>
          <div className="sidebar-toggle" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </div>
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            items={items}
            onClick={handleMenuClick}
            className="sidebar-menu"
          />
        </div>

        {user && (
          <div className="sidebar-footer">
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">{user.username || 'Signed in'}</span>
              {roleLabel && <span className="sidebar-user-role">{roleLabel}</span>}
            </div>
            <button
              type="button"
              className="sidebar-logout-btn"
              onClick={() => logout()}
              aria-label="Logout"
            >
              <LogoutOutlined />
              {!collapsed && <span>Logout</span>}
            </button>
          </div>
        )}
      </div>
    </Sider>
  )
}

export default Sidebar
