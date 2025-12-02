import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Input, Space, Tag, Select, Typography, Row, Col, message, Modal, Spin } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  ToolOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import MachineModal from '../components/modals/MachineModal'
import apiClient from '../utils/api'
import '../styles/machines.css'

const { Title } = Typography
const { Search } = Input
const { confirm } = Modal

interface Machine {
  key: string
  id: number
  name: string
  serial: string
  model: string
  site: string
  site_id?: number
  status: 'active' | 'inactive' | 'maintenance'
  lastMaintenance: string | null
  nextMaintenance: string | null
  cycle_count: number
}

const Machines: React.FC = () => {
  const [selectedSite, setSelectedSite] = useState<string>('all')
  const [showDecommissioned, setShowDecommissioned] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedMachine, setSelectedMachine] = useState<Machine | undefined>(undefined)
  const [machines, setMachines] = useState<Machine[]>([])
  const [loading, setLoading] = useState(true)
  const [sites, setSites] = useState<any[]>([])

  const fetchSites = async () => {
    try {
      const response = await apiClient.get('/api/v1/sites')
      setSites(response.data.data)
    } catch (error: any) {
      console.error('Failed to load sites:', error)
    }
  }

  const fetchMachines = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/machines')
      const machinesData = response.data.data.map((machine: any) => ({
        key: machine.id.toString(),
        id: machine.id,
        name: machine.name,
        serial: machine.serial || '',
        model: machine.model || '',
        site: machine.site || '',
        site_id: machine.site_id,
        status: machine.status || 'active',
        lastMaintenance: machine.lastMaintenance,
        nextMaintenance: machine.nextMaintenance,
        cycle_count: machine.cycle_count || 0,
      }))
      setMachines(machinesData)
    } catch (error: any) {
      console.error('Failed to load machines:', error)
      message.error('Failed to load machines')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSites()
    fetchMachines()
  }, [])

  // Listen for keyboard shortcuts
  useEffect(() => {
    const handleKeyboardNew = () => {
      handleCreateMachine()
    }
    const handleKeyboardRefresh = () => {
      fetchMachines()
      fetchSites()
      message.info('Refreshing machines...')
    }

    window.addEventListener('keyboard-new', handleKeyboardNew)
    window.addEventListener('keyboard-refresh', handleKeyboardRefresh)

    return () => {
      window.removeEventListener('keyboard-new', handleKeyboardNew)
      window.removeEventListener('keyboard-refresh', handleKeyboardRefresh)
    }
  }, [])

  const handleCreateMachine = () => {
    setSelectedMachine(undefined)
    setModalVisible(true)
  }

  const handleEditMachine = (machine: Machine) => {
    setSelectedMachine(machine)
    setModalVisible(true)
  }

  const handleDeleteMachine = (machine: Machine) => {
    confirm({
      title: 'Delete Machine',
      icon: <ExclamationCircleOutlined />,
      content: `Are you sure you want to delete "${machine.name}"?`,
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      async onOk() {
        try {
          await apiClient.post(`/machines/delete/${machine.id}`)
          message.success(`Machine "${machine.name}" deleted successfully`)
          await fetchMachines()
        } catch (error: any) {
          console.error('Failed to delete machine:', error)
          message.error('Failed to delete machine')
        }
      },
    })
  }

  const handleSubmitMachine = async (values: any) => {
    try {
      // Create FormData to match Flask's form handling
      const formData = new FormData()
      formData.append('name', values.name)
      formData.append('model', values.model || '')
      formData.append('serial_number', values.serial || '')
      formData.append('machine_number', values.machine_number || '')
      formData.append('site_id', values.site_id)

      if (selectedMachine) {
        // Update existing machine
        await apiClient.post(`/machine/edit/${selectedMachine.id}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        message.success('Machine updated successfully')
      } else {
        // Create new machine
        await apiClient.post('/machines', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        message.success('Machine created successfully')
      }
      
      // Refresh the machines list
      await fetchMachines()
      setModalVisible(false)
    } catch (error: any) {
      console.error('Failed to save machine:', error)
      message.error(error.response?.data?.message || 'Failed to save machine')
    }
  }

  const columns: ColumnsType<Machine> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Machine Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: 'Serial Number',
      dataIndex: 'serial',
      key: 'serial',
    },
    {
      title: 'Model',
      dataIndex: 'model',
      key: 'model',
    },
    {
        title: 'Site',
        dataIndex: 'site',
        key: 'site',
        filters: sites.map(site => ({
          text: site.name,
          value: site.name
        })),
        onFilter: (value, record) => record.site === value,
      },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = 'green'
        if (status === 'maintenance') color = 'orange'
        if (status === 'inactive') color = 'red'
        return <Tag color={color}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Last Maintenance',
      dataIndex: 'lastMaintenance',
      key: 'lastMaintenance',
      render: (date: string | null) => date || 'N/A',
      sorter: (a, b) => {
        const dateA = a.lastMaintenance ? new Date(a.lastMaintenance).getTime() : 0
        const dateB = b.lastMaintenance ? new Date(b.lastMaintenance).getTime() : 0
        return dateA - dateB
      },
    },
    {
      title: 'Next Maintenance',
      dataIndex: 'nextMaintenance',
      key: 'nextMaintenance',
      render: (date: string | null) => date || 'N/A',
      sorter: (a, b) => {
        const dateA = a.nextMaintenance ? new Date(a.nextMaintenance).getTime() : 0
        const dateB = b.nextMaintenance ? new Date(b.nextMaintenance).getTime() : 0
        return dateA - dateB
      },
    },
    {
      title: 'Cycles',
      dataIndex: 'cycle_count',
      key: 'cycle_count',
      width: 100,
      sorter: (a, b) => a.cycle_count - b.cycle_count,
      render: (count: number) => (
        <span style={{ fontFamily: 'monospace' }}>
          {count.toLocaleString()}
        </span>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            title="Edit"
            onClick={() => handleEditMachine(record)}
          />
          <Button
            type="text"
            icon={<ToolOutlined />}
            size="small"
            title="Maintenance"
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            size="small"
            title="Delete"
            onClick={() => handleDeleteMachine(record)}
          />
        </Space>
      ),
    },
  ]

  const handleSearch = (value: string) => {
    setSearchTerm(value)
  }

  return (
    <div className="machines-container">
      <div className="machines-header">
        <Title level={2}>Machines</Title>
      </div>

      <Row gutter={[16, 16]} className="machines-stats">
        <Col xs={24} sm={8}>
          <Card>
            <div className="stat-item">
              <span className="stat-label">Total Machines</span>
              <span className="stat-value">{machines.length}</span>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div className="stat-item">
              <span className="stat-label">Active</span>
              <span className="stat-value stat-active">
                {machines.filter((m) => m.status === 'active').length}
              </span>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div className="stat-item">
              <span className="stat-label">In Maintenance</span>
              <span className="stat-value stat-warning">
                {machines.filter((m) => m.status === 'maintenance').length}
              </span>
            </div>
          </Card>
        </Col>
      </Row>

      <Card className="machines-table-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div className="machines-controls">
            <Space wrap>
              <Search
                placeholder="Search machines, serial numbers..."
                allowClear
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: 300 }}
                prefix={<SearchOutlined />}
              />
              <Select
                value={selectedSite}
                onChange={setSelectedSite}
                style={{ width: 150 }}
                options={[
                  { value: 'all', label: 'All Sites' },
                  ...sites.map(site => ({
                    value: site.name,
                    label: site.name
                  }))
                ]}
              />
              <Button
                icon={<FilterOutlined />}
                onClick={() => setShowDecommissioned(!showDecommissioned)}
              >
                {showDecommissioned ? 'Hide' : 'Show'} Decommissioned
              </Button>
            </Space>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchMachines} loading={loading}>
                Refresh
              </Button>
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleCreateMachine}
              >
                Add Machine
              </Button>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={machines.filter(machine => {
              if (!searchTerm) return true
              const search = searchTerm.toLowerCase()
              return (
                machine.name.toLowerCase().includes(search) ||
                (machine.serial && machine.serial.toLowerCase().includes(search)) ||
                (machine.model && machine.model.toLowerCase().includes(search))
              )
            })}
            loading={loading}
            pagination={{
              pageSize: 25,
              showSizeChanger: true,
              pageSizeOptions: ['25', '50', '100'],
              showTotal: (total) => `Total ${total} machines`,
            }}
            scroll={{ x: 1200 }}
          />
        </Space>
      </Card>

      <MachineModal
        visible={modalVisible}
        machine={selectedMachine}
        sites={sites}
        onCancel={() => setModalVisible(false)}
        onSubmit={handleSubmitMachine}
      />
    </div>
  )
}

export default Machines
