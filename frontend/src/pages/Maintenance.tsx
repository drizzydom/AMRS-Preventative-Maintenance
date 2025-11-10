import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Input, Space, Select, Typography, message, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import MaintenanceCompletionModal from '../components/modals/MaintenanceCompletionModal'
import apiClient from '../utils/api'
import '../styles/maintenance.css'

const { Title } = Typography
const { Search } = Input

interface MaintenanceRecord {
  key: string
  id: number
  machine: string
  machineName: string
  part: string
  partName: string
  completedDate: string
  completedBy: string
  site: string
  siteName: string
  notes: string | null
}

interface Machine {
  id: number
  name: string
  site_name: string
}

interface Site {
  id: number
  name: string
}

const Maintenance: React.FC = () => {
  const [selectedSite, setSelectedSite] = useState<string>('all')
  const [searchText, setSearchText] = useState<string>('')
  const [completionModalVisible, setCompletionModalVisible] = useState(false)
  const [selectedMachine, setSelectedMachine] = useState<{ id: number; name: string } | null>(null)
  const [records, setRecords] = useState<MaintenanceRecord[]>([])
  const [filteredRecords, setFilteredRecords] = useState<MaintenanceRecord[]>([])
  const [machines, setMachines] = useState<Machine[]>([])
  const [sites, setSites] = useState<Site[]>([])
  const [loading, setLoading] = useState(true)

  const fetchMaintenanceHistory = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/maintenance/history')
      console.log('Maintenance history API response:', response.data)
      
      if (!response.data || !response.data.data) {
        console.warn('No data received from maintenance history API')
        setRecords([])
        setFilteredRecords([])
        return
      }
      
      const historyData = response.data.data.map((record: any) => ({
        key: record.id.toString(),
        id: record.id,
        machine: record.machine_id?.toString() || '',
        machineName: record.machine_name || record.machine || 'Unknown Machine',
        part: record.part_id?.toString() || '',
        partName: record.part_name || record.part || 'Unknown Part',
        completedDate: record.completed_date || record.date || record.created_at,
        completedBy: record.completed_by || record.user || 'N/A',
        site: record.site_id?.toString() || '',
        siteName: record.site_name || record.site || 'N/A',
        notes: record.notes || null,
      }))
      
      console.log(`Loaded ${historyData.length} maintenance records`)
      setRecords(historyData)
      setFilteredRecords(historyData)
    } catch (error: any) {
      console.error('Failed to load maintenance history:', error)
      console.error('Error details:', error.response?.data)
      message.error(error.response?.data?.error || 'Failed to load maintenance history')
      setRecords([])
      setFilteredRecords([])
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

  useEffect(() => {
    fetchMaintenanceHistory()
    fetchMachines()
    fetchSites()
  }, [])

  useEffect(() => {
    let filtered = records

    // Filter by site
    if (selectedSite && selectedSite !== 'all') {
      filtered = filtered.filter(record => record.siteName === selectedSite)
    }

    // Filter by search text
    if (searchText) {
      const search = searchText.toLowerCase()
      filtered = filtered.filter(record =>
        record.machineName.toLowerCase().includes(search) ||
        record.partName.toLowerCase().includes(search) ||
        record.completedBy.toLowerCase().includes(search) ||
        record.siteName.toLowerCase().includes(search)
      )
    }

    setFilteredRecords(filtered)
  }, [selectedSite, searchText, records])

  const handleAddMaintenance = () => {
    // Open modal without a pre-selected machine
    setSelectedMachine(null)
    setCompletionModalVisible(true)
  }

  const handleSelectMachine = (machineId: number) => {
    const machine = machines.find(m => m.id === machineId)
    if (machine) {
      setSelectedMachine({ id: machine.id, name: machine.name })
      setCompletionModalVisible(true)
    }
  }

  const columns: ColumnsType<MaintenanceRecord> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Date',
      dataIndex: 'completedDate',
      key: 'completedDate',
      width: 120,
      sorter: (a, b) => {
        const dateA = a.completedDate ? new Date(a.completedDate).getTime() : 0
        const dateB = b.completedDate ? new Date(b.completedDate).getTime() : 0
        return dateB - dateA // Most recent first
      },
      render: (date: string) => {
        if (!date) return 'N/A'
        return new Date(date).toLocaleDateString()
      },
    },
    {
      title: 'Machine',
      dataIndex: 'machineName',
      key: 'machineName',
      sorter: (a, b) => a.machineName.localeCompare(b.machineName),
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: 'Part',
      dataIndex: 'partName',
      key: 'partName',
      sorter: (a, b) => a.partName.localeCompare(b.partName),
    },
    {
      title: 'Site',
      dataIndex: 'siteName',
      key: 'siteName',
      width: 120,
      render: (site: string) => (
        <Tag color="blue">{site}</Tag>
      ),
    },
    {
      title: 'Completed By',
      dataIndex: 'completedBy',
      key: 'completedBy',
      width: 150,
    },
    {
      title: 'Notes',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
      render: (notes: string | null) => notes || '-',
    },
  ]

  // Get unique site names from records for the filter
  const siteOptions = [
    { value: 'all', label: 'All Sites' },
    ...Array.from(new Set(records.map(r => r.siteName)))
      .filter(Boolean)
      .map(site => ({ value: site, label: site }))
  ]

  return (
    <div className="maintenance-container">
      <div className="maintenance-header">
        <Title level={2}>
          <ToolOutlined /> Maintenance Records
        </Title>
        <p style={{ color: '#666', marginTop: 8 }}>
          Record and track maintenance activities performed on machines and parts
        </p>
      </div>

      <Card className="maintenance-table-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div className="maintenance-controls">
            <Space wrap>
              <Search
                placeholder="Search machines, parts, or people..."
                allowClear
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                style={{ width: 350 }}
                prefix={<SearchOutlined />}
              />
              <Select
                value={selectedSite}
                onChange={setSelectedSite}
                style={{ width: 180 }}
                options={siteOptions}
              />
            </Space>
            <Space>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={fetchMaintenanceHistory} 
                loading={loading}
              >
                Refresh
              </Button>
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleAddMaintenance}
              >
                Add Maintenance Record
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
                <strong>Total Records:</strong> {filteredRecords.length}
              </span>
              {selectedSite !== 'all' && (
                <span>
                  <strong>Site:</strong> {selectedSite}
                </span>
              )}
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={filteredRecords}
            loading={loading}
            locale={{
              emptyText: (
                <div style={{ padding: '40px 0' }}>
                  <ToolOutlined style={{ fontSize: 48, color: '#bfbfbf', marginBottom: 16 }} />
                  <h3 style={{ color: '#8c8c8c' }}>No Maintenance Records Found</h3>
                  <p style={{ color: '#bfbfbf', marginBottom: 16 }}>
                    Start recording maintenance activities by clicking "Add Maintenance Record" above.
                  </p>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={handleAddMaintenance}
                  >
                    Add First Record
                  </Button>
                </div>
              ),
            }}
            pagination={{
              pageSize: 25,
              showSizeChanger: true,
              pageSizeOptions: ['25', '50', '100', '200'],
              showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} records`,
            }}
            scroll={{ x: 1200 }}
          />
        </Space>
      </Card>

      <Card 
        title="Quick Access: Complete Multi-Part Maintenance" 
        className="maintenance-completion-card"
        style={{ marginTop: 20 }}
      >
        <p style={{ marginBottom: 16, color: '#666' }}>
          Select a machine to quickly complete maintenance on multiple parts at once. 
          This is useful for routine maintenance that affects several components.
        </p>
        <Space>
          <span style={{ fontWeight: 500 }}>Select Machine:</span>
          <Select
            style={{ width: 350 }}
            placeholder="Choose a machine..."
            showSearch
            optionFilterProp="children"
            onChange={handleSelectMachine}
            value={null}
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
            options={machines.map(machine => ({
              value: machine.id,
              label: `${machine.name} (${machine.site_name || 'No Site'})`,
            }))}
          />
        </Space>
      </Card>

      <MaintenanceCompletionModal
        open={completionModalVisible}
        machineId={selectedMachine?.id || 0}
        machineName={selectedMachine?.name || ''}
        onClose={() => {
          setCompletionModalVisible(false)
          setSelectedMachine(null)
        }}
        onComplete={() => {
          setCompletionModalVisible(false)
          setSelectedMachine(null)
          fetchMaintenanceHistory()
          message.success('Maintenance recorded successfully')
        }}
      />
    </div>
  )
}

export default Maintenance
