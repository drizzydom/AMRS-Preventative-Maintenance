import React, { useState, useEffect, useMemo } from 'react'
import { Card, Table, Button, Input, Space, Select, Typography, message, Tag, Switch, Collapse, Badge } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  ToolOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons'
import MaintenanceCompletionModal from '../components/modals/MaintenanceCompletionModal'
import MaintenanceDetailModal from '../components/modals/MaintenanceDetailModal'
import apiClient from '../utils/api'
import '../styles/maintenance.css'

const { Title } = Typography
const { Search } = Input
const { Panel } = Collapse

interface MaintenanceTask {
  key: string
  id: number
  part_name: string
  machine: string
  machine_name: string
  machine_id: number
  machine_serial?: string
  machine_cycle_count?: number
  task: string
  dueDate: string
  next_maintenance: string
  status: 'overdue' | 'due_soon' | 'completed' | 'ok' | 'pending'
  is_cycle_based?: boolean
  site: string
  site_name: string
  site_id: number
  lastMaintenance: string | null
  frequency: string | null
  days_overdue?: number
  days_until?: number
  // Cycle-based fields
  cycle_frequency?: number
  next_cycle?: number
  last_cycle?: number
  cycles_remaining?: number
  cycles_overdue?: number
}

interface Machine {
  id: number
  name: string
  serial: string
  site_name: string
  site_id: number
}

interface Site {
  id: number
  name: string
}

interface Part {
  id: number
  name: string
  description: string
}

// Grouped data structure for machine view
interface GroupedByMachine {
  machine_id: number
  machine_name: string
  machine_serial?: string
  site_id: number
  site_name: string
  tasks: MaintenanceTask[]
  overdue_count: number
  due_soon_count: number
}

const Maintenance: React.FC = () => {
  const [selectedSite, setSelectedSite] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [searchText, setSearchText] = useState<string>('')
  const [showInactive, setShowInactive] = useState<boolean>(false)
  const [groupByMachine, setGroupByMachine] = useState<boolean>(false)
  const [completionModalVisible, setCompletionModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null)
  const [selectedMachine, setSelectedMachine] = useState<{ id: number; name: string; site_id: number } | null>(null)
  const [tasks, setTasks] = useState<MaintenanceTask[]>([])
  const [filteredTasks, setFilteredTasks] = useState<MaintenanceTask[]>([])
  const [machines, setMachines] = useState<Machine[]>([])
  const [machineParts, setMachineParts] = useState<Part[]>([])
  const [sites, setSites] = useState<Site[]>([])
  const [loading, setLoading] = useState(true)

  // Group filtered tasks by machine for the grouped view
  const groupedByMachine = useMemo((): GroupedByMachine[] => {
    const groups: Record<number, GroupedByMachine> = {}
    
    filteredTasks.forEach(task => {
      if (!groups[task.machine_id]) {
        groups[task.machine_id] = {
          machine_id: task.machine_id,
          machine_name: task.machine_name,
          machine_serial: task.machine_serial,
          site_id: task.site_id,
          site_name: task.site_name,
          tasks: [],
          overdue_count: 0,
          due_soon_count: 0,
        }
      }
      groups[task.machine_id].tasks.push(task)
      if (task.status === 'overdue') groups[task.machine_id].overdue_count++
      if (task.status === 'due_soon') groups[task.machine_id].due_soon_count++
    })

    // Sort by site name, then machine name
    return Object.values(groups).sort((a, b) => {
      const siteCompare = a.site_name.localeCompare(b.site_name)
      if (siteCompare !== 0) return siteCompare
      return a.machine_name.localeCompare(b.machine_name)
    })
  }, [filteredTasks])

  // Group machines by site for the accordion headers
  const groupedBySite = useMemo(() => {
    const siteGroups: Record<string, GroupedByMachine[]> = {}
    
    groupedByMachine.forEach(machine => {
      const siteName = machine.site_name || 'No Site'
      if (!siteGroups[siteName]) {
        siteGroups[siteName] = []
      }
      siteGroups[siteName].push(machine)
    })

    return Object.entries(siteGroups).sort(([a], [b]) => a.localeCompare(b))
  }, [groupedByMachine])

  const fetchMaintenanceTasks = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/maintenance')
      console.log('Maintenance tasks API response:', response.data)
      
      if (!response.data || !response.data.data) {
        console.warn('No data received from maintenance API')
        setTasks([])
        setFilteredTasks([])
        return
      }
      
      const tasksData = response.data.data.map((task: any) => ({
        key: task.id.toString(),
        id: task.id,
        part_name: task.part_name || 'Unknown Service',
        machine: task.machine || task.machine_name || 'Unknown Machine',
        machine_name: task.machine_name || task.machine || 'Unknown Machine',
        machine_id: task.machine_id || 0,
        machine_serial: task.machine_serial,
        task: task.task || task.part_name || 'Unknown Task',
        dueDate: task.dueDate || task.next_maintenance || '',
        next_maintenance: task.next_maintenance || task.dueDate || '',
        status: task.status || 'pending',
        site: task.site || task.site_name || '',
        site_name: task.site_name || task.site || '',
        site_id: task.site_id || 0,
        lastMaintenance: task.lastMaintenance || null,
        frequency: task.frequency || null,
        days_overdue: task.days_overdue,
        days_until: task.days_until,
        // Cycle-based maintenance fields
        is_cycle_based: task.is_cycle_based || false,
        cycle_frequency: task.cycle_frequency || null,
        last_cycle: task.last_cycle || null,
        next_cycle: task.next_cycle || null,
        cycles_remaining: task.cycles_remaining || null,
      }))
      
      console.log(`Loaded ${tasksData.length} maintenance tasks`)
      setTasks(tasksData)
      setFilteredTasks(tasksData)
    } catch (error: any) {
      console.error('Failed to load maintenance tasks:', error)
      console.error('Error details:', error.response?.data)
      message.error(error.response?.data?.error || 'Failed to load maintenance tasks')
      setTasks([])
      setFilteredTasks([])
    } finally {
      setLoading(false)
    }
  }

  const fetchMachines = async () => {
    try {
      const response = await apiClient.get('/api/v1/machines')
      if (response.data && response.data.data) {
        setMachines(response.data.data)
      }
    } catch (error: any) {
      console.error('Failed to load machines:', error)
      message.error('Failed to load machines')
    }
  }

  const fetchSites = async () => {
    try {
      const response = await apiClient.get('/api/v1/sites')
      if (response.data && response.data.data) {
        setSites(response.data.data)
      }
    } catch (error: any) {
      console.error('Failed to load sites:', error)
      message.error('Failed to load sites')
    }
  }

  const fetchMachineParts = async (machineId: number) => {
    try {
      const response = await apiClient.get(`/api/v1/machines/${machineId}/parts`)
      if (response.data && response.data.data) {
        setMachineParts(response.data.data)
      }
    } catch (error: any) {
      console.error('Failed to load machine parts:', error)
      message.error('Failed to load machine services')
    }
  }

  useEffect(() => {
    fetchMaintenanceTasks()
    fetchMachines()
    fetchSites()
  }, [])

  // Listen for keyboard shortcuts
  useEffect(() => {
    const handleKeyboardRefresh = () => {
      fetchMaintenanceTasks()
      fetchMachines()
      fetchSites()
      message.info('Refreshing maintenance tasks...')
    }
    const handleKeyboardEscape = () => {
      setCompletionModalVisible(false)
      setDetailModalVisible(false)
    }

    window.addEventListener('keyboard-refresh', handleKeyboardRefresh)
    window.addEventListener('keyboard-escape', handleKeyboardEscape)

    return () => {
      window.removeEventListener('keyboard-refresh', handleKeyboardRefresh)
      window.removeEventListener('keyboard-escape', handleKeyboardEscape)
    }
  }, [])

  useEffect(() => {
    let filtered = tasks

    // Filter out inactive tasks (last maintenance before 2015) unless showInactive is true
    if (!showInactive) {
      filtered = filtered.filter(task => {
        if (!task.lastMaintenance) return true // Keep tasks with no history
        const lastMaintenanceYear = new Date(task.lastMaintenance).getFullYear()
        return lastMaintenanceYear >= 2015
      })
    }

    // Filter by site
    if (selectedSite && selectedSite !== 'all') {
      const siteId = parseInt(selectedSite)
      filtered = filtered.filter(task => task.site_id === siteId)
    }

    // Filter by status
    if (selectedStatus && selectedStatus !== 'all') {
      filtered = filtered.filter(task => task.status === selectedStatus)
    }

    // Filter by search text
    if (searchText) {
      const search = searchText.toLowerCase()
      filtered = filtered.filter(task =>
        task.machine_name.toLowerCase().includes(search) ||
        task.part_name.toLowerCase().includes(search) ||
        task.task.toLowerCase().includes(search) ||
        task.site_name.toLowerCase().includes(search) ||
        (task.machine_serial && task.machine_serial.toLowerCase().includes(search))
      )
    }

    setFilteredTasks(filtered)
  }, [selectedSite, selectedStatus, searchText, showInactive, tasks])

  const handleAddMaintenance = () => {
    // Open modal without a pre-selected machine
    setSelectedMachine(null)
    setCompletionModalVisible(true)
  }

  const handleSelectMachine = async (machineId: number) => {
    const machine = machines.find(m => m.id === machineId)
    if (machine) {
      setSelectedMachine({ id: machine.id, name: machine.name, site_id: machine.site_id })
      await fetchMachineParts(machine.id)
      setCompletionModalVisible(true)
    }
  }

  const handleSiteFilterChange = (value: string) => {
    setSelectedSite(value)
    // Reset machine selection when site changes
    setSelectedMachine(null)
  }

  const columns: ColumnsType<MaintenanceTask> = [
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      sorter: (a, b) => {
        const statusOrder: Record<string, number> = { overdue: 0, due_soon: 1, ok: 2, pending: 2, completed: 3 }
        return (statusOrder[a.status] || 2) - (statusOrder[b.status] || 2)
      },
      render: (status: string, record: MaintenanceTask) => {
        if (status === 'overdue') {
          // Show cycles or days depending on maintenance type
          const detail = record.is_cycle_based 
            ? (record.cycles_overdue ? `(${record.cycles_overdue} cycles)` : '')
            : (record.days_overdue ? `(${record.days_overdue}d)` : '')
          return (
            <Tag color="red" icon={<WarningOutlined />}>
              Overdue {detail}
            </Tag>
          )
        } else if (status === 'due_soon') {
          const detail = record.is_cycle_based
            ? (record.cycles_remaining ? `(${record.cycles_remaining} cycles)` : '')
            : (record.days_until ? `(${record.days_until}d)` : '')
          return (
            <Tag color="orange" icon={<ClockCircleOutlined />}>
              Due Soon {detail}
            </Tag>
          )
        } else if (status === 'ok' || status === 'pending') {
          const detail = record.is_cycle_based
            ? (record.cycles_remaining ? `${record.cycles_remaining} cycles left` : '')
            : (record.days_until ? `${record.days_until} days left` : '')
          return <Tag color="green">{detail || 'OK'}</Tag>
        } else {
          return <Tag color="green">Completed</Tag>
        }
      },
    },
    {
      title: 'Machine',
      dataIndex: 'machine_name',
      key: 'machine_name',
      sorter: (a, b) => a.machine_name.localeCompare(b.machine_name),
      render: (text: string, record: MaintenanceTask) => (
        <div>
          <strong>{text}</strong>
          {record.machine_serial && (
            <div style={{ fontSize: '12px', color: '#666' }}>S/N: {record.machine_serial}</div>
          )}
          {record.is_cycle_based && record.machine_cycle_count !== undefined && (
            <div style={{ fontSize: '11px', color: '#1890ff' }}>
              Cycles: {record.machine_cycle_count.toLocaleString()}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Service / Task',
      dataIndex: 'part_name',
      key: 'part_name',
      sorter: (a, b) => a.part_name.localeCompare(b.part_name),
      render: (text: string, record: MaintenanceTask) => {
        // Clean up task name: remove duplicate machine name if present
        let displayName = text
        if (record.task && record.task.includes(' - ')) {
          const parts = record.task.split(' - ')
          // If first part is machine name and duplicated, remove it
          if (parts[0] === parts[1]) {
            displayName = parts.slice(1).join(' - ')
          } else if (parts.length === 3 && parts[0] === parts[1]) {
            // Handle case like "Machine - Machine - Part"
            displayName = `${parts[0]} - ${parts[2]}`
          } else {
            displayName = record.task
          }
        }
        return (
          <div>
            {displayName}
            {record.is_cycle_based && (
              <Tag color="purple" style={{ marginLeft: 8, fontSize: '10px' }}>Cycle-Based</Tag>
            )}
          </div>
        )
      },
    },
    {
      title: 'Site',
      dataIndex: 'site_name',
      key: 'site_name',
      width: 120,
      render: (site: string) => (
        <Tag color="blue">{site}</Tag>
      ),
    },
    {
      title: 'Due Date',
      dataIndex: 'dueDate',
      key: 'dueDate',
      width: 120,
      sorter: (a, b) => {
        const dateA = a.dueDate ? new Date(a.dueDate).getTime() : 0
        const dateB = b.dueDate ? new Date(b.dueDate).getTime() : 0
        return dateA - dateB
      },
      render: (date: string) => {
        if (!date) return 'N/A'
        return new Date(date).toLocaleDateString()
      },
    },
    {
      title: 'Last Maintenance',
      dataIndex: 'lastMaintenance',
      key: 'lastMaintenance',
      width: 140,
      render: (date: string | null) => {
        if (!date) return <span style={{ color: '#999' }}>Never</span>
        return new Date(date).toLocaleDateString()
      },
    },
    {
      title: 'Frequency',
      dataIndex: 'frequency',
      key: 'frequency',
      width: 140,
      render: (freq: string | null, record: MaintenanceTask) => {
        if (record.is_cycle_based && record.cycle_frequency) {
          return (
            <div>
              <div style={{ fontWeight: 500 }}>Every {record.cycle_frequency.toLocaleString()} cycles</div>
              {record.next_cycle && (
                <div style={{ fontSize: '11px', color: '#666' }}>
                  Next: {record.next_cycle.toLocaleString()}
                </div>
              )}
            </div>
          )
        }
        return freq || '-'
      },
    },
  ]

  // Get site options from fetched sites
  const siteOptions = [
    { value: 'all', label: 'All Sites' },
    ...sites.map(site => ({ value: site.id.toString(), label: site.name }))
  ]

  const statusOptions = [
    { value: 'all', label: 'All Status' },
    { value: 'overdue', label: 'Overdue' },
    { value: 'due_soon', label: 'Due Soon' },
    { value: 'completed', label: 'Completed' },
  ]

  // Get machines filtered by selected site for the quick access section
  const filteredMachines = selectedSite === 'all' 
    ? machines 
    : machines.filter(m => m.site_id.toString() === selectedSite)

  return (
    <div className="maintenance-container">
      <div className="maintenance-header">
        <Title level={2}>
          <ToolOutlined /> Maintenance Tasks
        </Title>
        <p style={{ color: '#666', marginTop: 8 }}>
          Track and complete scheduled maintenance for machines and services
        </p>
      </div>

      {/* Quick Access Multi-Part Maintenance - Moved to top */}
      <Card 
        title="Quick Access: Complete Multi-Service Maintenance" 
        className="maintenance-completion-card"
        style={{ marginBottom: 20 }}
      >
        <p style={{ marginBottom: 16, color: '#666' }}>
          Select a site and machine to quickly complete maintenance on multiple services at once. 
          This is useful for routine maintenance that affects several components.
        </p>
        <Space wrap>
          <span style={{ fontWeight: 500 }}>Site:</span>
          <Select
            style={{ width: 200 }}
            placeholder="Select a site..."
            value={selectedSite}
            onChange={handleSiteFilterChange}
            options={siteOptions}
          />
          <span style={{ fontWeight: 500 }}>Machine:</span>
          <Select
            style={{ width: 350 }}
            placeholder="Choose a machine..."
            showSearch
            optionFilterProp="children"
            onChange={handleSelectMachine}
            value={selectedMachine?.id || null}
            disabled={!filteredMachines.length}
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
            options={filteredMachines.map(machine => ({
              value: machine.id,
              label: machine.serial 
                ? `${machine.name} - S/N: ${machine.serial} (${machine.site_name || 'No Site'})`
                : `${machine.name} (${machine.site_name || 'No Site'})`,
            }))}
          />
        </Space>
      </Card>

      <Card className="maintenance-table-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div className="maintenance-controls">
            <Space wrap>
              <Search
                placeholder="Search machines, serial numbers, services..."
                allowClear
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                style={{ width: 300 }}
                prefix={<SearchOutlined />}
              />
              <Select
                value={selectedSite}
                onChange={setSelectedSite}
                style={{ width: 180 }}
                options={siteOptions}
                placeholder="Filter by site"
              />
              <Select
                value={selectedStatus}
                onChange={setSelectedStatus}
                style={{ width: 180 }}
                options={statusOptions}
                placeholder="Filter by status"
              />
              <Space>
                <span style={{ fontSize: '14px', color: '#666' }}>Show Inactive:</span>
                <Switch 
                  checked={showInactive}
                  onChange={setShowInactive}
                  checkedChildren="Yes"
                  unCheckedChildren="No"
                />
              </Space>
              <Space>
                <span style={{ fontSize: '14px', color: '#666' }}>Group by Machine:</span>
                <Switch 
                  checked={groupByMachine}
                  onChange={setGroupByMachine}
                  checkedChildren="Yes"
                  unCheckedChildren="No"
                />
              </Space>
            </Space>
            <Space>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={fetchMaintenanceTasks} 
                loading={loading}
              >
                Refresh
              </Button>
            </Space>
          </div>

          <div style={{ 
            padding: '12px 16px', 
            background: '#f0f2f5', 
            borderRadius: 4,
            marginBottom: 8 
          }}>
            <Space size="large">
              <span>
                <strong>Total Tasks:</strong> {filteredTasks.length}
              </span>
              {selectedSite !== 'all' && (
                <span>
                  <strong>Site:</strong> {sites.find(s => s.id.toString() === selectedSite)?.name}
                </span>
              )}
              {selectedStatus !== 'all' && (
                <span>
                  <strong>Status:</strong> {selectedStatus.replace('_', ' ').toUpperCase()}
                </span>
              )}
              {!showInactive && (
                <span style={{ color: '#999', fontSize: '13px' }}>
                  (Hiding tasks last maintained before 2015)
                </span>
              )}
            </Space>
          </div>

          {groupByMachine ? (
            /* Grouped by Machine View */
            <div className="grouped-maintenance-view">
              {groupedBySite.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center' }}>
                  <ToolOutlined style={{ fontSize: 48, color: '#bfbfbf', marginBottom: 16 }} />
                  <h3 style={{ color: '#8c8c8c' }}>No Maintenance Tasks Found</h3>
                  <p style={{ color: '#bfbfbf' }}>
                    {!showInactive 
                      ? 'Try enabling "Show Inactive" to see older maintenance tasks.'
                      : 'No maintenance tasks match your current filters.'}
                  </p>
                </div>
              ) : (
                groupedBySite.map(([siteName, siteMachines]) => (
                  <div key={siteName} style={{ marginBottom: 24 }}>
                    <Typography.Title level={4} style={{ 
                      background: '#1890ff', 
                      color: 'white', 
                      padding: '8px 16px', 
                      borderRadius: '4px 4px 0 0',
                      margin: 0 
                    }}>
                      {siteName}
                      <Badge 
                        count={siteMachines.reduce((sum: number, m: GroupedByMachine) => sum + m.tasks.length, 0)} 
                        style={{ backgroundColor: '#52c41a', marginLeft: 12 }} 
                        overflowCount={999}
                      />
                    </Typography.Title>
                    <Collapse 
                      defaultActiveKey={siteMachines.slice(0, 3).map((m: GroupedByMachine) => m.machine_id.toString())}
                      style={{ borderRadius: '0 0 4px 4px' }}
                    >
                      {siteMachines.map((machine: GroupedByMachine) => (
                        <Collapse.Panel
                          key={machine.machine_id.toString()}
                          header={
                            <Space size="middle">
                              <span style={{ fontWeight: 600 }}>{machine.machine_name}</span>
                              {machine.machine_serial && (
                                <Tag color="blue">S/N: {machine.machine_serial}</Tag>
                              )}
                              <Badge count={machine.tasks.length} style={{ backgroundColor: '#1890ff' }} />
                              {machine.overdue_count > 0 && (
                                <Tag color="red" icon={<WarningOutlined />}>
                                  {machine.overdue_count} Overdue
                                </Tag>
                              )}
                              {machine.due_soon_count > 0 && (
                                <Tag color="orange" icon={<ClockCircleOutlined />}>
                                  {machine.due_soon_count} Due Soon
                                </Tag>
                              )}
                            </Space>
                          }
                        >
                          <Table
                            columns={columns}
                            dataSource={machine.tasks}
                            pagination={false}
                            size="small"
                            onRow={(record) => ({
                              onClick: () => {
                                setSelectedRecordId(record.id)
                                setDetailModalVisible(true)
                              },
                              style: { cursor: 'pointer' }
                            })}
                            scroll={{ x: 1200 }}
                          />
                        </Collapse.Panel>
                      ))}
                    </Collapse>
                  </div>
                ))
              )}
            </div>
          ) : (
            /* Standard Table View */
            <Table
              columns={columns}
              dataSource={filteredTasks}
              loading={loading}
              onRow={(record) => ({
                onClick: () => {
                  setSelectedRecordId(record.id)
                  setDetailModalVisible(true)
                },
                style: { cursor: 'pointer' }
              })}
              locale={{
                emptyText: (
                  <div style={{ padding: '40px 0' }}>
                    <ToolOutlined style={{ fontSize: 48, color: '#bfbfbf', marginBottom: 16 }} />
                    <h3 style={{ color: '#8c8c8c' }}>No Maintenance Tasks Found</h3>
                    <p style={{ color: '#bfbfbf', marginBottom: 16 }}>
                      {!showInactive 
                        ? 'Try enabling "Show Inactive" to see older maintenance tasks.'
                        : 'No maintenance tasks match your current filters.'}
                    </p>
                  </div>
                ),
              }}
              pagination={{
                pageSize: 25,
                showSizeChanger: true,
                pageSizeOptions: ['25', '50', '100', '200'],
                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} tasks`,
              }}
              scroll={{ x: 1400 }}
            />
          )}
        </Space>
      </Card>

      <MaintenanceCompletionModal
        open={completionModalVisible}
        machineId={selectedMachine?.id || null}
        machineName={selectedMachine?.name || ''}
        onClose={() => {
          setCompletionModalVisible(false)
          setSelectedMachine(null)
        }}
        onComplete={() => {
          setCompletionModalVisible(false)
          setSelectedMachine(null)
          fetchMaintenanceTasks()
          message.success('Maintenance recorded successfully')
        }}
      />

      <MaintenanceDetailModal
        open={detailModalVisible}
        onClose={() => {
          setDetailModalVisible(false)
          setSelectedRecordId(null)
        }}
        recordId={selectedRecordId}
      />
    </div>
  )
}

export default Maintenance
