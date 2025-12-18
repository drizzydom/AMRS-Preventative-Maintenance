import React, { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Row, Col, Statistic, Table, Button, Space, Typography, Spin, message, Collapse, Badge, Switch, Tag } from 'antd'
import {
  ToolOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
  EnvironmentOutlined,
  DownOutlined,
  RightOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import apiClient from '../utils/api'
import { notifyOverdueItems } from '../utils/notifications'
import EmergencyMaintenanceModal from '../components/modals/EmergencyMaintenanceModal'
import '../styles/dashboard.css'

const { Title, Text } = Typography
const { Panel } = Collapse

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
  machine_serial?: string
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
  machine_serial?: string
  site_name: string
  site_id?: number
  days_until: number
  next_maintenance: string
}

// Grouped data structures
interface GroupedBySite {
  site_name: string
  site_id: number
  machines: GroupedByMachine[]
  overdue_count: number
  due_soon_count: number
}

interface GroupedByMachine {
  machine_name: string
  machine_id: number
  tasks: (OverdueItem | DueSoonItem)[]
  overdue_count: number
  due_soon_count: number
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [overdueItems, setOverdueItems] = useState<OverdueItem[]>([])
  const [dueSoonItems, setDueSoonItems] = useState<DueSoonItem[]>([])
  const [sites, setSites] = useState<{id:number; name:string}[]>([])
  const [selectedSite, setSelectedSite] = useState<number | 'all'>('all')
  const [loading, setLoading] = useState(true)
  const [groupByMachine, setGroupByMachine] = useState(true)
  const [showDecommissioned, setShowDecommissioned] = useState(false)
  const [emergencyModalOpen, setEmergencyModalOpen] = useState(false)
  
  // Group items by site and machine
  const groupedData = useMemo(() => {
    const allItems = [
      ...overdueItems.map(item => ({ ...item, type: 'overdue' as const })),
      ...dueSoonItems.map(item => ({ ...item, type: 'due_soon' as const }))
    ]
    
    // Filter by selected site
    const filtered = selectedSite === 'all' 
      ? allItems 
      : allItems.filter(item => item.site_id === selectedSite)
    
    // Group by site
    const siteGroups: Record<number, GroupedBySite> = {}
    
    filtered.forEach(item => {
      const siteId = item.site_id || 0
      const siteName = item.site_name || 'Unknown Site'
      
      if (!siteGroups[siteId]) {
        siteGroups[siteId] = {
          site_name: siteName,
          site_id: siteId,
          machines: [],
          overdue_count: 0,
          due_soon_count: 0
        }
      }
      
      if (item.type === 'overdue') siteGroups[siteId].overdue_count++
      else siteGroups[siteId].due_soon_count++
      
      // Find or create machine group
      const machineId = item.machine_id || 0
      let machineGroup = siteGroups[siteId].machines.find(m => m.machine_id === machineId)
      
      if (!machineGroup) {
        machineGroup = {
          machine_name: item.machine_name || 'Unknown Machine',
          machine_id: machineId,
          tasks: [],
          overdue_count: 0,
          due_soon_count: 0
        }
        siteGroups[siteId].machines.push(machineGroup)
      }
      
      machineGroup.tasks.push(item)
      if (item.type === 'overdue') machineGroup.overdue_count++
      else machineGroup.due_soon_count++
    })
    
    // Sort by site name
    return Object.values(siteGroups).sort((a, b) => a.site_name.localeCompare(b.site_name))
  }, [overdueItems, dueSoonItems, selectedSite])

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
    { title: 'Service', dataIndex: 'part_name', key: 'part_name' },
    { 
      title: 'Machine', 
      dataIndex: 'machine_name', 
      key: 'machine_name',
      render: (text: string, record: any) => (
        <span>
          {text}
          {record.machine_serial && (
            <Text type="secondary" style={{ marginLeft: 8, fontSize: '0.9em' }}>
              (S/N: {record.machine_serial})
            </Text>
          )}
        </span>
      )
    },
    { title: 'Site', dataIndex: 'site_name', key: 'site_name' },
    { title: 'Days Overdue', dataIndex: 'days_overdue', key: 'days_overdue', render: (d: number) => <span style={{ color: '#ff4d4f', fontWeight: 600 }}>{d} days</span> },
    { title: 'Next Maintenance', dataIndex: 'next_maintenance', key: 'next_maintenance' },
  ]

  const dueSoonColumns = [
    { title: 'Service', dataIndex: 'part_name', key: 'part_name' },
    { 
      title: 'Machine', 
      dataIndex: 'machine_name', 
      key: 'machine_name',
      render: (text: string, record: any) => (
        <span>
          {text}
          {record.machine_serial && (
            <Text type="secondary" style={{ marginLeft: 8, fontSize: '0.9em' }}>
              (S/N: {record.machine_serial})
            </Text>
          )}
        </span>
      )
    },
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

  // Task columns for the grouped tables
  const taskColumns = [
    { 
      title: 'Service', 
      dataIndex: 'part_name', 
      key: 'part_name',
      render: (text: string, record: any) => (
        <span>
          {text}
          {record.type === 'overdue' ? (
            <Tag color="red" style={{ marginLeft: 8 }}>Overdue</Tag>
          ) : (
            <Tag color="orange" style={{ marginLeft: 8 }}>Due Soon</Tag>
          )}
        </span>
      )
    },
    { 
      title: 'Due', 
      key: 'due',
      render: (_: any, record: any) => {
        if (record.days_overdue !== undefined) {
          return <span style={{ color: '#ff4d4f', fontWeight: 600 }}>{record.days_overdue}d overdue</span>
        }
        return <span style={{ color: '#faad14' }}>{record.days_until}d left</span>
      }
    },
    { title: 'Next Maintenance', dataIndex: 'next_maintenance', key: 'next_maintenance' },
  ]

  return (
    <div className="dashboard-container">
      <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <Title level={2} style={{ margin: 0 }}>Dashboard</Title>
          <div>
            <label style={{ marginRight: 8, color: '#666' }}>Site:</label>
            <select 
              value={selectedSite === 'all' ? 'all' : String(selectedSite)} 
              onChange={(e) => setSelectedSite(e.target.value === 'all' ? 'all' : Number(e.target.value))}
              style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid #d9d9d9' }}
            >
              <option value="all">All Sites</option>
              {sites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Switch 
              checked={groupByMachine} 
              onChange={setGroupByMachine}
              size="small"
            />
            <Text type="secondary">Group by Site/Machine</Text>
          </div>
        </div>
        <Space>
          <Button 
            danger 
            icon={<ThunderboltOutlined />} 
            onClick={() => setEmergencyModalOpen(true)}
          >
            Emergency Maintenance
          </Button>
          <Button type="primary" onClick={() => navigate('/maintenance')}>Record Maintenance</Button>
          <Button onClick={() => { /* TODO: Export report */ }}>Export Report</Button>
          <Button icon={<ReloadOutlined />} onClick={fetchDashboardData}>Refresh</Button>
        </Space>
      </div>

      {/* Emergency Maintenance Modal */}
      <EmergencyMaintenanceModal
        open={emergencyModalOpen}
        onClose={() => setEmergencyModalOpen(false)}
        onSuccess={() => fetchDashboardData()}
      />

      {/* Stats Row */}
      <Row gutter={[16, 16]} className="stats-row">
        {statsData.map((stat, index) => (
          <Col xs={24} sm={12} md={6} key={index}>
            <Card hoverable onClick={() => {
              if (stat.title === 'Overdue') navigate('/maintenance')
              else if (stat.title === 'Due Soon') navigate('/maintenance')
              else if (stat.title === 'Total Machines') navigate('/machines')
            }}>
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

      {/* Grouped View */}
      {groupByMachine ? (
        <Card title="Maintenance Overview by Site" style={{ marginTop: 16 }}>
          {groupedData.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
              <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              <div style={{ marginTop: 16 }}>All maintenance is up to date!</div>
            </div>
          ) : (
            <Collapse 
              defaultActiveKey={groupedData.length <= 3 ? groupedData.map(s => s.site_id.toString()) : []}
              expandIcon={({ isActive }) => isActive ? <DownOutlined /> : <RightOutlined />}
            >
              {groupedData.map(site => (
                <Panel 
                  key={site.site_id.toString()} 
                  header={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <EnvironmentOutlined style={{ color: '#1890ff' }} />
                      <strong>{site.site_name}</strong>
                      {site.overdue_count > 0 && (
                        <Badge count={site.overdue_count} style={{ backgroundColor: '#ff4d4f' }} />
                      )}
                      {site.due_soon_count > 0 && (
                        <Badge count={site.due_soon_count} style={{ backgroundColor: '#faad14' }} />
                      )}
                      <Text type="secondary">({site.machines.length} machines)</Text>
                    </div>
                  }
                >
                  <Collapse 
                    ghost
                    expandIcon={({ isActive }) => isActive ? <DownOutlined /> : <RightOutlined />}
                  >
                    {site.machines.map(machine => (
                      <Panel
                        key={machine.machine_id.toString()}
                        header={
                          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <ToolOutlined />
                            <span>
                              {machine.machine_name}
                              {machine.tasks[0]?.machine_serial && (
                                <Text type="secondary" style={{ marginLeft: 8, fontSize: '0.9em' }}>
                                  (S/N: {machine.tasks[0].machine_serial})
                                </Text>
                              )}
                            </span>
                            {machine.overdue_count > 0 && (
                              <Tag color="red">{machine.overdue_count} overdue</Tag>
                            )}
                            {machine.due_soon_count > 0 && (
                              <Tag color="orange">{machine.due_soon_count} due soon</Tag>
                            )}
                          </div>
                        }
                      >
                        <Table
                          columns={taskColumns}
                          dataSource={machine.tasks}
                          rowKey="id"
                          pagination={false}
                          size="small"
                        />
                      </Panel>
                    ))}
                  </Collapse>
                </Panel>
              ))}
            </Collapse>
          )}
        </Card>
      ) : (
        <>
          <Card title={`Overdue Maintenance (${filteredOverdue.length})`} className="mb-4" style={{ marginTop: 16 }}>
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
        </>
      )}
    </div>
  )
}

export default Dashboard
