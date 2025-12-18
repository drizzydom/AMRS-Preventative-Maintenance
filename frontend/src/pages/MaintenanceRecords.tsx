import React, { useCallback, useEffect, useState } from 'react'
import { Card, Table, Select, Space, Typography, Tag, Input, Button, message } from 'antd'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import { FileTextOutlined, ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import apiClient from '../utils/api'
import '../styles/maintenance-records.css'

const { Title, Text } = Typography
const { Search } = Input

interface MaintenanceRecordRow {
  id: number
  machine: string
  machine_id: number | null
  machine_serial?: string
  part: string
  part_id: number | null
  site: string
  site_id: number | null
  completedDate: string
  completedBy: string
  maintenanceType: string
  status: string
  notes: string
}

interface SiteOption {
  id: number
  name: string
}

interface MachineOption {
  id: number
  name: string
  site_id: number
  site_name: string
  machine_number?: string
  serial?: string
}

interface PartOption {
  id: number
  name: string
}

const statusColorMap: Record<string, string> = {
  completed: 'green',
  pending: 'orange',
  overdue: 'red',
}

const MaintenanceRecords: React.FC = () => {
  const [records, setRecords] = useState<MaintenanceRecordRow[]>([])
  const [sites, setSites] = useState<SiteOption[]>([])
  const [machines, setMachines] = useState<MachineOption[]>([])
  const [parts, setParts] = useState<PartOption[]>([])
  const [selectedSite, setSelectedSite] = useState<string>('all')
  const [selectedMachine, setSelectedMachine] = useState<number | null>(null)
  const [selectedPart, setSelectedPart] = useState<number | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [totalRecords, setTotalRecords] = useState(0)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchSites()
    fetchMachines()
  }, [])

  const fetchSites = async () => {
    try {
      const response = await apiClient.get('/api/v1/sites')
      if (response.data?.data) {
        setSites(response.data.data)
      }
    } catch (error) {
      console.error('Failed to load sites', error)
      message.error('Unable to load sites')
    }
  }

  const fetchMachines = async () => {
    try {
      const response = await apiClient.get('/api/v1/machines')
      if (response.data?.data) {
        setMachines(response.data.data)
      }
    } catch (error) {
      console.error('Failed to load machines', error)
      message.error('Unable to load machines')
    }
  }

  const fetchParts = useCallback(async (machineId: number) => {
    try {
      const response = await apiClient.get(`/api/v1/machines/${machineId}/parts`)
      if (response.data?.data) {
        const partOptions = response.data.data.map((part: any) => ({
          id: part.id,
          name: part.name,
        }))
        setParts(partOptions)
      }
    } catch (error) {
      console.error('Failed to load parts', error)
      message.error('Unable to load services for machine')
    }
  }, [])

  useEffect(() => {
    if (selectedMachine) {
      fetchParts(selectedMachine)
      setSelectedPart(null)
    } else {
      setParts([])
      setSelectedPart(null)
    }
  }, [fetchParts, selectedMachine])

  const fetchRecords = useCallback(async () => {
    setLoading(true)
    try {
      const response = await apiClient.get('/api/v1/maintenance/history', {
        params: {
          page,
          page_size: pageSize,
          site_id: selectedSite,
          machine_id: selectedMachine || undefined,
          part_id: selectedPart || undefined,
          search: searchTerm || undefined,
        }
      })
      const data = response.data?.data || {}
      const serverPagination = data.pagination || {}
      const total = serverPagination.total_records || 0
      const totalPages = serverPagination.total_pages || (total && Math.ceil(total / pageSize)) || 0
      if (totalPages && page > totalPages) {
        setPage(totalPages)
        return
      }
      setRecords(data.records || [])
      setTotalRecords(total)
    } catch (error: any) {
      console.error('Failed to load maintenance records', error)
      const errorMsg = error.response?.data?.error || 'Unable to load maintenance records'
      message.error(errorMsg)
      setRecords([])
      setTotalRecords(0)
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, selectedSite, selectedMachine, selectedPart, searchTerm])

  useEffect(() => {
    fetchRecords()
  }, [fetchRecords])

  const handleTableChange = (paginationConfig: TablePaginationConfig) => {
    if (paginationConfig.current) {
      setPage(paginationConfig.current)
    }
    if (paginationConfig.pageSize && paginationConfig.pageSize !== pageSize) {
      setPageSize(paginationConfig.pageSize)
      setPage(1)
    }
  }

  const handleSiteChange = (value: string) => {
    setSelectedSite(value)
    setSelectedMachine(null)
    setSelectedPart(null)
    setParts([])
    setPage(1)
  }

  const handleMachineChange = (value: number | null | undefined) => {
    setSelectedMachine(value ?? null)
    setSelectedPart(null)
    setPage(1)
  }

  const handlePartChange = (value: number | null | undefined) => {
    setSelectedPart(value ?? null)
    setPage(1)
  }

  const handleSearch = (value: string) => {
    setSearchInput(value)
    setSearchTerm(value.trim())
    setPage(1)
  }

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value
    setSearchInput(value)
    if (!value) {
      setSearchTerm('')
      setPage(1)
    }
  }

  const handleResetFilters = () => {
    setSelectedSite('all')
    setSelectedMachine(null)
    setSelectedPart(null)
    setParts([])
    setSearchInput('')
    setSearchTerm('')
    setPage(1)
    setPageSize(25)
  }

  const filteredMachines = selectedSite === 'all'
    ? machines
    : machines.filter((machine) => machine.site_id?.toString() === selectedSite)

  const columns: ColumnsType<MaintenanceRecordRow> = [
    {
      title: 'Completed',
      dataIndex: 'completedDate',
      key: 'completedDate',
      width: 140,
      sorter: (a, b) => {
        const aTime = a.completedDate ? dayjs(a.completedDate).valueOf() : 0
        const bTime = b.completedDate ? dayjs(b.completedDate).valueOf() : 0
        return aTime - bTime
      },
      render: (value: string) => (value ? dayjs(value).format('MMM D, YYYY') : '-'),
    },
    {
      title: 'Machine',
      dataIndex: 'machine',
      key: 'machine',
      render: (_value: string, record) => (
        <div>
          <strong>{record.machine || 'Unknown'}</strong>
          {record.machine_serial && (
            <div style={{ fontSize: '12px', color: '#666' }}>S/N: {record.machine_serial}</div>
          )}
          {record.site && (
            <div>
              <Tag color="blue" style={{ marginTop: 4 }}>{record.site}</Tag>
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Service',
      dataIndex: 'part',
      key: 'part',
      render: (value: string) => value || 'Unknown',
    },
    {
      title: 'Type',
      dataIndex: 'maintenanceType',
      key: 'maintenanceType',
      width: 140,
      render: (value: string) => <Tag color="purple">{value || 'Scheduled'}</Tag>,
    },
    {
      title: 'Completed By',
      dataIndex: 'completedBy',
      key: 'completedBy',
      width: 160,
      render: (value: string) => value || 'Unknown',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (value: string) => (
        <Tag color={statusColorMap[value] || 'default'}>{value ? value.replace('_', ' ').toUpperCase() : 'COMPLETED'}</Tag>
      )
    },
    {
      title: 'Notes',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
      render: (value: string) => value || '-',
    }
  ]

  const rangeStart = totalRecords === 0 ? 0 : (page - 1) * pageSize + 1
  const rangeEnd = totalRecords === 0 ? 0 : Math.min(page * pageSize, totalRecords)

  return (
    <div className="maintenance-records-container">
      <div className="maintenance-records-header">
        <Title level={2}>
          <Space size="small">
            <FileTextOutlined />
            <span>Maintenance Records</span>
          </Space>
        </Title>
        <p>Browse completed maintenance with per-site filters and fast pagination.</p>
      </div>

      <Card>
        <div className="maintenance-records-filters">
          <Select
            style={{ minWidth: 180 }}
            value={selectedSite}
            onChange={handleSiteChange}
            options={[
              { value: 'all', label: 'All Sites' },
              ...sites.map((site) => ({ value: site.id.toString(), label: site.name })),
            ]}
          />

          <Select
            style={{ minWidth: 220 }}
            value={selectedMachine ?? undefined}
            placeholder="Machine"
            onChange={handleMachineChange}
            allowClear
            options={filteredMachines.map((machine) => ({
              value: machine.id,
              label: machine.serial
                ? `${machine.name} - S/N: ${machine.serial}`
                : `${machine.name} (${machine.site_name || 'No Site'})`
            }))}
          />

          <Select
            style={{ minWidth: 200 }}
            value={selectedPart ?? undefined}
            placeholder="Service"
            onChange={handlePartChange}
            allowClear
            options={parts.map((part) => ({ value: part.id, label: part.name }))}
            disabled={!selectedMachine}
          />

          <Search
            placeholder="Search machine, service, notes..."
            value={searchInput}
            onChange={handleSearchChange}
            onSearch={handleSearch}
            allowClear
            style={{ minWidth: 240 }}
          />

          <Space>
            <Button onClick={() => fetchRecords()} icon={<ReloadOutlined />}>
              Refresh
            </Button>
            <Button onClick={handleResetFilters}>Reset Filters</Button>
          </Space>
        </div>
      </Card>

      <Card className="maintenance-records-table-card">
        <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
          <Text type="secondary">
            Showing {rangeStart} - {rangeEnd} of {totalRecords} records
          </Text>
        </Space>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={records}
          loading={loading}
          onChange={handleTableChange}
          pagination={{
            current: page,
            pageSize,
            total: totalRecords,
            showSizeChanger: true,
            pageSizeOptions: ['10', '25', '50', '100'],
          }}
        />
      </Card>
    </div>
  )
}

export default MaintenanceRecords
