import React from 'react'
import { Card, Table, Button, Input, Space, Tag, Typography, Row, Col, Statistic } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons'
import '../styles/sites.css'

const { Title } = Typography
const { Search } = Input

interface Site {
  key: string
  id: number
  name: string
  location: string
  machineCount: number
  activeCount: number
  maintenanceThreshold: number
  contactPerson: string
  phone: string
  status: 'active' | 'inactive'
}

const Sites: React.FC = () => {
  // Mock data - will be replaced with API calls
  const mockData: Site[] = [
    {
      key: '1',
      id: 1,
      name: 'Main Plant',
      location: 'Building A, Floor 1',
      machineCount: 45,
      activeCount: 42,
      maintenanceThreshold: 7,
      contactPerson: 'John Manager',
      phone: '555-0101',
      status: 'active',
    },
    {
      key: '2',
      id: 2,
      name: 'Warehouse',
      location: 'Building B',
      machineCount: 28,
      activeCount: 25,
      maintenanceThreshold: 14,
      contactPerson: 'Jane Supervisor',
      phone: '555-0102',
      status: 'active',
    },
    {
      key: '3',
      id: 3,
      name: 'Assembly Line',
      location: 'Building A, Floor 2',
      machineCount: 67,
      activeCount: 64,
      maintenanceThreshold: 7,
      contactPerson: 'Bob Foreman',
      phone: '555-0103',
      status: 'active',
    },
  ]

  const columns: ColumnsType<Site> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Site Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text) => (
        <Space>
          <EnvironmentOutlined style={{ color: '#1890ff' }} />
          <strong>{text}</strong>
        </Space>
      ),
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: 'Total Machines',
      dataIndex: 'machineCount',
      key: 'machineCount',
      sorter: (a, b) => a.machineCount - b.machineCount,
      render: (count) => <Tag color="blue">{count}</Tag>,
    },
    {
      title: 'Active Machines',
      dataIndex: 'activeCount',
      key: 'activeCount',
      sorter: (a, b) => a.activeCount - b.activeCount,
      render: (count) => <Tag color="green">{count}</Tag>,
    },
    {
      title: 'Maintenance Threshold (days)',
      dataIndex: 'maintenanceThreshold',
      key: 'maintenanceThreshold',
      sorter: (a, b) => a.maintenanceThreshold - b.maintenanceThreshold,
    },
    {
      title: 'Contact Person',
      dataIndex: 'contactPerson',
      key: 'contactPerson',
    },
    {
      title: 'Phone',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
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
            danger
            icon={<DeleteOutlined />}
            size="small"
            title="Delete"
          />
        </Space>
      ),
    },
  ]

  const totalMachines = mockData.reduce((sum, site) => sum + site.machineCount, 0)
  const totalActive = mockData.reduce((sum, site) => sum + site.activeCount, 0)

  return (
    <div className="sites-container">
      <div className="sites-header">
        <Title level={2}>Sites Management</Title>
      </div>

      <Row gutter={[16, 16]} className="sites-stats">
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Sites"
              value={mockData.length}
              prefix={<EnvironmentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Machines"
              value={totalMachines}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Active Machines"
              value={totalActive}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Inactive Machines"
              value={totalMachines - totalActive}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Card className="sites-table-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div className="sites-controls">
            <Search
              placeholder="Search sites..."
              allowClear
              style={{ width: 300 }}
              prefix={<SearchOutlined />}
            />
            <Space>
              <Button icon={<ReloadOutlined />}>Refresh</Button>
              <Button type="primary" icon={<PlusOutlined />}>
                Add Site
              </Button>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={mockData}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              pageSizeOptions: ['10', '20', '50'],
              showTotal: (total) => `Total ${total} sites`,
            }}
          />
        </Space>
      </Card>
    </div>
  )
}

export default Sites
