import React, { useState } from 'react'
import { Card, Table, Button, Input, Space, Tag, Select, Typography, Row, Col } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import '../styles/machines.css'

const { Title } = Typography
const { Search } = Input

interface Machine {
  key: string
  id: number
  name: string
  serial: string
  model: string
  site: string
  status: 'active' | 'inactive' | 'maintenance'
  lastMaintenance: string
  nextMaintenance: string
}

const Machines: React.FC = () => {
  const [selectedSite, setSelectedSite] = useState<string>('all')
  const [showDecommissioned, setShowDecommissioned] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  // Mock data - will be replaced with API calls
  const mockData: Machine[] = [
    {
      key: '1',
      id: 1,
      name: 'CNC Machine A',
      serial: 'SN-001',
      model: 'Model X',
      site: 'Main Plant',
      status: 'active',
      lastMaintenance: '2025-10-15',
      nextMaintenance: '2025-11-15',
    },
    {
      key: '2',
      id: 2,
      name: 'Lathe Machine B',
      serial: 'SN-002',
      model: 'Model Y',
      site: 'Warehouse',
      status: 'maintenance',
      lastMaintenance: '2025-10-20',
      nextMaintenance: '2025-11-10',
    },
    {
      key: '3',
      id: 3,
      name: 'Press Machine C',
      serial: 'SN-003',
      model: 'Model Z',
      site: 'Main Plant',
      status: 'active',
      lastMaintenance: '2025-10-01',
      nextMaintenance: '2025-12-01',
    },
  ]

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
      filters: [
        { text: 'Main Plant', value: 'Main Plant' },
        { text: 'Warehouse', value: 'Warehouse' },
      ],
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
      sorter: (a, b) => new Date(a.lastMaintenance).getTime() - new Date(b.lastMaintenance).getTime(),
    },
    {
      title: 'Next Maintenance',
      dataIndex: 'nextMaintenance',
      key: 'nextMaintenance',
      sorter: (a, b) => new Date(a.nextMaintenance).getTime() - new Date(b.nextMaintenance).getTime(),
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
          />
        </Space>
      ),
    },
  ]

  const handleSearch = (value: string) => {
    setSearchTerm(value)
    // TODO: Implement search functionality
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
              <span className="stat-value">{mockData.length}</span>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div className="stat-item">
              <span className="stat-label">Active</span>
              <span className="stat-value stat-active">
                {mockData.filter((m) => m.status === 'active').length}
              </span>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div className="stat-item">
              <span className="stat-label">In Maintenance</span>
              <span className="stat-value stat-warning">
                {mockData.filter((m) => m.status === 'maintenance').length}
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
                placeholder="Search machines..."
                allowClear
                onSearch={handleSearch}
                style={{ width: 300 }}
                prefix={<SearchOutlined />}
              />
              <Select
                value={selectedSite}
                onChange={setSelectedSite}
                style={{ width: 150 }}
                options={[
                  { value: 'all', label: 'All Sites' },
                  { value: 'main', label: 'Main Plant' },
                  { value: 'warehouse', label: 'Warehouse' },
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
              <Button icon={<ReloadOutlined />}>Refresh</Button>
              <Button type="primary" icon={<PlusOutlined />}>
                Add Machine
              </Button>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={mockData}
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
    </div>
  )
}

export default Machines
