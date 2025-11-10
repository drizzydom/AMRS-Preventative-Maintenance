import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Button, Space, Typography, Spin, message } from 'antd'
import {
  ToolOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import apiClient from '../utils/api'
import { notifyOverdueItems } from '../utils/notifications'
import '../styles/dashboard.css'

const { Title } = Typography

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
  machine_id?: number
  site_name: string
  site_id?: number
  days_overdue: number
  next_maintenance: string
}

interface DueSoonItem {
  id: number
  part_name: string
  machine_name: string
  machine_id?: number
  site_name: string
  site_id?: number
  days_until: number
  next_maintenance: string
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [overdueItems, setOverdueItems] = useState<OverdueItem[]>([])
  const [dueSoonItems, setDueSoonItems] = useState<DueSoonItem[]>([])
  const [sites, setSites] = useState<{id:number; name:string}[]>([])
  const [selectedSite, setSelectedSite] = useState<number | 'all'>('all')
  const [loading, setLoading] = useState(true)

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      console.log('[Dashboard] Fetching dashboard data...')

      // Fetch stats
      console.log('[Dashboard] Fetching stats from /api/v1/dashboard')
      const statsResp = await apiClient.get('/api/v1/dashboard')
      console.log('[Dashboard] Stats response:', statsResp.data)
      setStats(statsResp.data.data)

      // Fetch overdue items
      console.log('[Dashboard] Fetching overdue items from /api/v1/maintenance?status=overdue')
      const overdueResp = await apiClient.get('/api/v1/maintenance?status=overdue')
      console.log('[Dashboard] Overdue items response:', overdueResp.data)
      const overdueData = Array.isArray(overdueResp.data.data) ? overdueResp.data.data : []
      console.log(`[Dashboard] Loaded ${overdueData.length} overdue items`)
      setOverdueItems(overdueData)

      // Fetch due soon items
      console.log('[Dashboard] Fetching due soon items from /api/v1/maintenance?status=due_soon')
      const dueSoonResp = await apiClient.get('/api/v1/maintenance?status=due_soon')
      console.log('[Dashboard] Due soon items response:', dueSoonResp.data)
      const dueSoonData = Array.isArray(dueSoonResp.data.data) ? dueSoonResp.data.data : []
      console.log(`[Dashboard] Loaded ${dueSoonData.length} due soon items`)
      setDueSoonItems(dueSoonData)

      console.log('[Dashboard] All data loaded successfully')
    } catch (error: any) {
      console.error('[Dashboard] Failed to load dashboard data:', error)
      console.error('[Dashboard] Error details:', error.response?.data)
      const errorMsg = error.response?.data?.error || 'Failed to load dashboard data'
      message.error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
    // also load sites for filtering
    fetchSites()
  }, [])

  // Listen for socket-sync events to refresh dashboard
  useEffect(() => {
    const handleSync = () => {
      console.log('[Dashboard] Socket sync event received, refreshing data...')
      fetchDashboardData()
    }

    window.addEventListener('socket-sync', handleSync)
    return () => window.removeEventListener('socket-sync', handleSync)
  }, [])

  // Listen for keyboard refresh shortcut
  useEffect(() => {
    const handleRefresh = () => {
      console.log('[Dashboard] Keyboard refresh triggered')
      fetchDashboardData()
    }

    window.addEventListener('keyboard-refresh', handleRefresh)
    return () => window.removeEventListener('keyboard-refresh', handleRefresh)
  }, [])

  // Show notification for overdue items (only once per session)
  useEffect(() => {
    if (stats && stats.overdue > 0) {
      // Check if we've already notified in this session
      const hasNotified = sessionStorage.getItem('overdue-notified')
      if (!hasNotified) {
        notifyOverdueItems(stats.overdue)
        sessionStorage.setItem('overdue-notified', 'true')
      }
    }
  }, [stats])

  const fetchSites = async () => {
    try {
      const resp = await apiClient.get('/api/v1/sites')
      if (Array.isArray(resp.data.data)) setSites(resp.data.data)
    } catch (e) {
      console.warn('Failed to load sites for dashboard filter', e)
    }
  }

  const statsData = stats ? [
    { title: 'Total Machines', value: stats.total_machines, icon: <ToolOutlined />, color: '#1890ff' },
    { title: 'Overdue', value: stats.overdue, icon: <WarningOutlined />, color: '#ff4d4f' },
    { title: 'Due Soon', value: stats.due_soon, icon: <ClockCircleOutlined />, color: '#faad14' },
    { title: 'Completed (This Month)', value: stats.completed, icon: <CheckCircleOutlined />, color: '#52c41a' },
  ] : []

  const overdueColumns = [
    { title: 'Part', dataIndex: 'part_name', key: 'part_name' },
    { title: 'Machine', dataIndex: 'machine_name', key: 'machine_name' },
    { title: 'Site', dataIndex: 'site_name', key: 'site_name' },
    { title: 'Days Overdue', dataIndex: 'days_overdue', key: 'days_overdue', render: (d: number) => <span style={{ color: '#ff4d4f', fontWeight: 600 }}>{d} days</span> },
    { title: 'Next Maintenance', dataIndex: 'next_maintenance', key: 'next_maintenance' },
  ]

  const dueSoonColumns = [
    { title: 'Part', dataIndex: 'part_name', key: 'part_name' },
    { title: 'Machine', dataIndex: 'machine_name', key: 'machine_name' },
    { title: 'Site', dataIndex: 'site_name', key: 'site_name' },
    { title: 'Due In', dataIndex: 'days_until', key: 'days_until', render: (d: number) => <span style={{ color: '#faad14' }}>{d} days</span> },
    { title: 'Next Maintenance', dataIndex: 'next_maintenance', key: 'next_maintenance' },
  ]

  // compute filtered lists when site filter is active
  const filteredOverdue = selectedSite === 'all' ? overdueItems : overdueItems.filter(i => i.site_id === selectedSite)
  const filteredDueSoon = selectedSite === 'all' ? dueSoonItems : dueSoonItems.filter(i => i.site_id === selectedSite)

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spin size="large" tip="Loading dashboard data..." />
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Title level={2} style={{ margin: 0 }}>Dashboard</Title>
          <div>
            <label style={{ marginRight: 8, color: '#666' }}>Filter by Site:</label>
            <select value={selectedSite === 'all' ? 'all' : String(selectedSite)} onChange={(e) => setSelectedSite(e.target.value === 'all' ? 'all' : Number(e.target.value))}>
              <option value="all">All Sites</option>
              {sites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
        </div>
        <Space>
          <Button type="primary" onClick={() => window.location.assign('/maintenance')}>Record Maintenance</Button>
          <Button onClick={() => { /* TODO: Export report */ }}>Export Report</Button>
          <Button icon={<ReloadOutlined />} onClick={fetchDashboardData}>Refresh</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} className="stats-row">
        {statsData.map((stat, index) => (
          <Col xs={24} sm={12} md={6} key={index}>
            <Card>
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={stat.icon}
                valueStyle={{ color: stat.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Card title={`Overdue Maintenance (${filteredOverdue.length})`} className="mb-4">
        <Table
          columns={overdueColumns}
          dataSource={filteredOverdue}
          rowKey={(record: OverdueItem) => record.id}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Card title={`Due Soon (${filteredDueSoon.length})`} className="mb-4">
        <Table
          columns={dueSoonColumns}
          dataSource={filteredDueSoon}
          rowKey={(record: DueSoonItem) => record.id}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

export default Dashboard
